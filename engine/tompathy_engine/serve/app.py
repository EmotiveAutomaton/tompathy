import asyncio
import hmac
import json
import re
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event, Lock
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .. import __version__
from ..admission import Admissions
from ..ledger.ids import canonical
from ..ledger.schema import Model
from ..ledger.store import Ledger
from ..packet.build import build_packet
from ..packet.contract import Artifact


class AnalysisRequest(Model):
    requestId: str = Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9_-]+$")
    artifact: Artifact
    scope: Literal["artifact", "context"]
    context: list[dict[str, Any]] = Field(default_factory=list, max_length=30)
    history: Literal["wikipedia"] | None = None


class Cancelled(Exception):
    pass


@dataclass
class Job:
    cancelled: Event = field(default_factory=Event)
    events: list[dict] = field(default_factory=list)
    lock: Lock = field(default_factory=Lock)
    started: float = field(default_factory=time.monotonic)

    def progress(self, phase):
        if self.cancelled.is_set():
            raise Cancelled()
        with self.lock:
            self.events.append({"phase": phase})


def load_token(path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="ascii") as stream:
            stream.write(secrets.token_hex(32))
        path.chmod(0o600)
    except FileExistsError:
        pass
    token = path.read_text(encoding="ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{64}", token):
        raise ValueError("Token file must contain a 256-bit hexadecimal token")
    return token


class BodyLimit:
    def __init__(self, app, maximum=2_000_000):
        self.app, self.maximum = app, maximum

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.maximum:
                return await JSONResponse({"detail": "Request exceeds 2 MB"}, 413)(
                    scope, receive, send
                )
            if not message.get("more_body", False):
                break
        first = True

        async def bounded_receive():
            nonlocal first
            if first:
                first = False
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)


def create_app(
    *,
    token,
    origins=(),
    ledger_path=None,
    admissions=None,
    builder=None,
    population_dir=None,
    model=None,
    goals=None,
    history_dir=None,
    reader=None,
    history_questions=(),
    history_fetcher=None,
):
    if not re.fullmatch(r"[0-9a-f]{64}", token):
        raise ValueError("Companion requires a 256-bit token")
    if any(not re.fullmatch(r"chrome-extension://[a-p]{32}", origin) for origin in origins):
        raise ValueError("CORS origins must be exact Chrome extension origins")
    gates = admissions or Admissions()
    ledger = Ledger(ledger_path) if ledger_path else None
    jobs, futures = {}, {}

    @asynccontextmanager
    async def lifespan(app):
        app.state.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tompathy")
        try:
            yield
        finally:
            for job in jobs.values():
                job.cancelled.set()
            app.state.pool.shutdown(wait=True, cancel_futures=True)

    app = FastAPI(
        title="ToMpathy local companion",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(BodyLimit)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(origins),
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
        allow_credentials=False,
    )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        # Do not echo captured page text into an error; encode JS edge surrogates
        # safely even when rejecting a malformed request.
        detail = [{k: e[k] for k in ("loc", "msg", "type")} for e in exc.errors()]
        return Response(
            content=canonical({"detail": detail}), status_code=422, media_type="application/json"
        )

    @app.middleware("http")
    async def authenticate(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and origin not in origins:
            return JSONResponse({"detail": "Origin not allowed"}, status_code=403)
        if request.method != "OPTIONS":
            supplied = request.headers.get("authorization", "")
            if not hmac.compare_digest(supplied, f"Bearer {token}"):
                return JSONResponse({"detail": "Authentication required"}, status_code=401)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/v1/health")
    async def health():
        return {
            "engineVersion": __version__,
            "implementationHash": gates.implementation,
            "admittedModules": gates.enabled("writing"),
            "ledgerRecords": len(ledger.all()) if ledger else 0,
            "modelsAvailable": [model.population] if model else [],
            "transcriberEnabled": reader is not None,
            "historyQuestions": list(history_questions),
            "historyAvailable": ["wikipedia"] if history_dir else [],
        }

    def execute(body, job):
        job.progress("Validating captured evidence")
        if builder:
            packet = builder(body, job)
        elif body.history:
            if history_dir is None:
                raise ValueError(
                    "History requests are disabled; configure --history-dir explicitly"
                )
            if body.scope != "artifact":
                raise ValueError("History requests use artifact scope")
            from ..workflow import analyze_history

            try:
                packet, _ = analyze_history(
                    body.artifact.model_dump(exclude_unset=True),
                    directory=history_dir,
                    questions=history_questions,
                    admissions=gates,
                    reader=reader,
                    progress=job.progress,
                    cancel=job.cancelled.is_set,
                    **({"fetcher": history_fetcher} if history_fetcher else {}),
                )
            except InterruptedError:
                raise Cancelled()
        else:
            packet = build_packet(
                body.artifact.model_dump(exclude_unset=True),
                ledger=ledger,
                scope=body.scope,
                context=body.context,
                admissions=gates,
                request_id=body.requestId,
                model=model,
                goals=goals,
            )
        job.progress("Packet validated")
        return packet

    @app.post("/v1/analyze")
    async def analyze(body: AnalysisRequest, request: Request):
        for key in list(jobs):
            if futures[key].done() and time.monotonic() - jobs[key].started > 300:
                del jobs[key], futures[key]
        if body.requestId in jobs:
            raise HTTPException(409, "Request ID already used")
        if any(not f.done() for f in futures.values()):
            raise HTTPException(409, "One CPU analysis is already running")
        if len(jobs) >= 100:
            oldest = min(jobs, key=lambda key: jobs[key].started)
            del jobs[oldest], futures[oldest]
        job = jobs[body.requestId] = Job()
        future = futures[body.requestId] = asyncio.get_running_loop().run_in_executor(
            app.state.pool, execute, body, job
        )
        if "text/event-stream" in request.headers.get("accept", ""):

            async def stream():
                cursor = 0
                try:
                    while not future.done():
                        if await request.is_disconnected():
                            job.cancelled.set()
                            return
                        with job.lock:
                            updates = job.events[cursor:]
                            cursor = len(job.events)
                        for update in updates:
                            yield "event: progress\ndata: " + json.dumps(update) + "\n\n"
                        await asyncio.sleep(0.05)
                    result = await future
                    yield "event: packet\ndata: " + json.dumps(result, ensure_ascii=True) + "\n\n"
                except Cancelled:
                    yield "event: cancelled\ndata: {}\n\n"
                except Exception:  # noqa: BLE001 -- streamed failures must not echo captured text
                    yield 'event: error\ndata: {"message":"Analysis failed; inspect local service log"}\n\n'
                finally:
                    if not future.done():
                        job.cancelled.set()

            return StreamingResponse(stream(), media_type="text/event-stream")
        try:
            return Response(content=canonical(await future), media_type="application/json")
        except Cancelled:
            raise HTTPException(409, "Analysis cancelled")
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        except asyncio.CancelledError:
            job.cancelled.set()
            raise

    @app.delete("/v1/analyze/{request_id}")
    async def cancel(request_id: str):
        if request_id not in jobs:
            raise HTTPException(404, "Unknown request")
        jobs[request_id].cancelled.set()
        return {"requestId": request_id, "status": "cancellation-requested"}

    @app.get("/v1/population/{population_id}")
    async def population(population_id: str):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", population_id):
            raise HTTPException(422, "Invalid population identifier")
        if population_dir:
            path = Path(population_dir) / (population_id + ".json")
            if path.is_file() and path.stat().st_size <= 2_000_000:
                value = json.loads(path.read_text(encoding="utf8"))
                if value.get("populationId") != population_id:
                    raise HTTPException(422, "Population identity mismatch")
                return value
        raise HTTPException(404, "No population summary is loaded")

    return app
