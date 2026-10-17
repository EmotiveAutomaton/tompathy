import asyncio
import hmac
import json
import logging
import re
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, asynccontextmanager
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
    history: Literal["wikipedia", "github"] | None = None
    historyLimit: int = Field(default=20, ge=1, le=500)
    githubToken: str | None = Field(default=None, min_length=1, max_length=500, repr=False)
    mode: Literal["admitted", "preview"] = "admitted"
    preferCache: bool = False
    priorityRegion: str | None = Field(default=None, max_length=200)
    compactProgress: bool = False


class Cancelled(Exception):
    pass


@dataclass
class Job:
    cancelled: Event = field(default_factory=Event)
    events: list[dict] = field(default_factory=list)
    lock: Lock = field(default_factory=Lock)
    started: float = field(default_factory=time.monotonic)
    partial_packet: dict | None = None
    partial_revision: int = 0

    def progress(self, phase):
        if self.cancelled.is_set():
            raise Cancelled()
        with self.lock:
            self.events.append({"phase": phase})

    def check(self):
        if self.cancelled.is_set():
            raise Cancelled()

    def publish(self, packet):
        self.check()
        with self.lock:
            self.partial_packet = packet
            self.partial_revision += 1


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
    preview_readers=(),
    preview_goals=None,
    preview_techniques=None,
    preview_correction_reader=None,
    preview_cache=None,
    preview_budget=165,
):
    if type(preview_budget) is not int or not 165 <= preview_budget <= 600:
        raise ValueError("Preview preparation budget must be 165–600 seconds")
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
        with ExitStack() as stack:
            try:
                backend = getattr(reader, "backend", None)
                if hasattr(backend, "session"):
                    stack.enter_context(backend.session())
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
            "refusedModules": gates.refused("writing"),
            "ledgerRecords": len(ledger.all()) if ledger else 0,
            "modelsAvailable": [model.population] if model else [],
            "transcriberEnabled": reader is not None,
            "historyQuestions": list(history_questions),
            "historyAvailable": ["wikipedia", "github"] if history_dir else [],
            "previewAvailable": True,
            "previewReaders": [r.identity for r in preview_readers],
        }

    def execute(body, job):
        job.progress("Validating captured evidence")
        backup_key = None
        if body.mode == "preview":
            from ..ledger.ids import digest
            from ..packet.contract import Packet
            from ..preview.cache import read as cache_read

            requested = body.model_dump(exclude_unset=False)
            for field in ("requestId", "githubToken", "preferCache", "priorityRegion", "compactProgress"):
                requested.pop(field, None)
            requested["artifact"].pop("capturedAt", None)
            backup_key = digest(["preview-request-v1", gates.implementation, requested,
                                 [r.identity for r in preview_readers], bool(preview_goals),
                                 bool(preview_techniques), getattr(preview_correction_reader, "pin", None),
                                 getattr(preview_goals, "identity", None), getattr(preview_techniques, "identity", None)])
            if body.preferCache:
                cached = cache_read(preview_cache, "requests", backup_key)
                if not cached:
                    raise ValueError("No matching cached real preview is available. Run Analyze capture or the source history action first.")
                packet = Packet.model_validate(cached["data"]).wire()
                packet["preview"]["cachedAt"] = cached["at"]
                job.progress("Loaded a cached real reading from " + cached["at"])
                return packet
        history_payload, history_error, history_cached_at = None, None, None
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
                from ..adapters.github import fetch_history as fetch_github
                from ..adapters.wiki import fetch_history as fetch_wiki
                from ..ledger.ids import digest
                from ..preview.cache import read as cache_read
                from ..preview.cache import write as cache_write
                history_key = digest(["github-parent-witness-v2" if body.history == "github" else "wikipedia-v1", body.artifact.id, body.artifact.source, body.historyLimit])
                cached = cache_read(preview_cache, "history", history_key, max_age=21600)
                if cached:
                    github_payload = cached["data"]
                    history_cached_at = cached["at"]
                    job.progress("Using cached public history fetched " + history_cached_at)
                else:
                    fetcher = fetch_github if body.history == "github" else history_fetcher or fetch_wiki
                    github_payload = fetcher(body.artifact.source, artifact_id=body.artifact.id, limit=body.historyLimit,
                        cancel=lambda: job.cancelled.is_set() or time.monotonic() - job.started > 30,
                        **({"token": body.githubToken} if body.history == "github" else {}))
                    cache_write(preview_cache, "history", history_key, github_payload)
                packet, history_receipt = analyze_history(
                    body.artifact.model_dump(exclude_unset=True),
                    directory=history_dir,
                    questions=history_questions,
                    admissions=gates,
                    reader=reader,
                    limit=body.historyLimit,
                    payload=github_payload,
                    adapter="git" if body.history == "github" else "wikipedia",
                    progress=job.progress,
                    cancel=lambda: job.cancelled.is_set() or body.mode == "preview" and time.monotonic() - job.started > 30,
                    **({"fetcher": history_fetcher} if history_fetcher else {}),
                )
                if body.mode == "preview":
                    history_payload = json.loads((Path(history_receipt["snapshot"]) / "source.json").read_text(encoding="utf8"))
            except InterruptedError:
                job.check()
                if body.mode != "preview":
                    raise Cancelled()
                history_error = "Public history exceeded its 30-second budget. The captured page can still be read; try fewer records or a cached run."
            except Exception:
                job.check()
                if body.mode != "preview":
                    raise
                history_error = "Public history could not be reconstructed. The captured page is still being read. Check the source license, quota and connection before retrying history."
                logging.getLogger("tompathy_engine").exception("Public history unavailable; retaining captured-page preview")
            if history_error:
                packet = build_packet(body.artifact.model_dump(exclude_unset=True), admissions=gates, request_id=body.requestId)
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
        if body.mode == "preview":
            from copy import deepcopy

            from ..ledger.ids import digest
            from ..packet.contract import Packet
            from ..preview.build import build_preview
            from ..preview.cache import keeps_progress
            from ..preview.cache import read as cache_read
            from ..preview.cache import write as cache_write
            inputs = deepcopy(packet)
            inputs.pop("id", None)
            inputs["artifact"].pop("capturedAt", None)
            captured_ids = {digest([body.artifact.revision, r.id]) for r in body.artifact.regions}
            for item in inputs["evidence"]:
                if item["id"] in captured_ids:
                    item.pop("capturedAt", None)
            cache_key = digest([gates.implementation, inputs, history_payload, [r.identity for r in preview_readers],
                                bool(preview_goals), bool(preview_techniques), getattr(preview_correction_reader, "pin", None),
                                getattr(preview_goals, "identity", None), getattr(preview_techniques, "identity", None)])
            cached = cache_read(preview_cache, "packets", cache_key) if not history_error else None
            if cached:
                packet = Packet.model_validate(cached["data"]).wire()
                packet["preview"]["cachedAt"] = cached["at"]
                job.progress("Loaded a cached real reading from " + cached["at"])
                return packet
            checkpoint = cache_read(preview_cache, "requests", backup_key) if not history_error else None
            best = checkpoint["data"] if checkpoint else None
            priority = checkpoint["data"].get("preview", {}).get("priorityRegion") if checkpoint else body.priorityRegion
            saved_at = 0.0
            def publish_partial(value):
                nonlocal saved_at, best
                job.publish(value)
                if not history_error and time.monotonic() - saved_at >= 2 and (best is None or keeps_progress(value, best)):
                    saved_at = time.monotonic()
                    backup = deepcopy(value)
                    backup["preview"]["resumable"] = True
                    cache_write(preview_cache, "requests", backup_key, backup)
                    best = backup
            packet = build_preview(packet, readers=preview_readers, goal_runner=preview_goals,
                                   technique_runner=preview_techniques, progress=job.progress,
                                   history=history_payload, correction_reader=preview_correction_reader,
                                   history_adapter="git" if body.history == "github" else "wikipedia",
                                   partial=publish_partial, check=job.check, deadline=job.started + preview_budget, history_error=history_error,
                                   priority_region=priority)
            if history_cached_at:
                packet["preview"]["modules"].append({"id": "history", "title": "Source history", "status": "complete", "detail": "Cached public history fetched " + history_cached_at})
            if best is not None and not keeps_progress(packet, best):
                packet = deepcopy(best)
                packet["preview"]["resumable"] = True
                job.progress("Retained the previous reading; exact cached work will be reused on continuation")
            if not history_error and all(m["status"] in {"complete", "unavailable"} for m in packet["preview"]["modules"]):
                cache_write(preview_cache, "packets", cache_key, packet)
            if not history_error:
                cache_write(preview_cache, "backups", cache_key, packet)
                cache_write(preview_cache, "requests", backup_key, packet)
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
                partial_revision = 0
                previous_partial = None
                try:
                    while not future.done():
                        if await request.is_disconnected():
                            job.cancelled.set()
                            return
                        with job.lock:
                            updates = job.events[cursor:]
                            cursor = len(job.events)
                            partial_packet = job.partial_packet if job.partial_revision != partial_revision else None
                            partial_revision = job.partial_revision
                        for update in updates:
                            yield "event: progress\ndata: " + json.dumps(update) + "\n\n"
                        if partial_packet:
                            event, data = "partial", partial_packet
                            if body.compactProgress and previous_partial:
                                # Replace whole top-level fields, never apply arbitrary paths.
                                # Immutable captured text/evidence is sent only once.
                                event = "partial-update"
                                data = {key: value for key, value in partial_packet.items() if value != previous_partial.get(key)}
                                data.update({key: None for key in previous_partial if key not in partial_packet})
                            yield "event: " + event + "\ndata: " + json.dumps(data, ensure_ascii=True) + "\n\n"
                            previous_partial = partial_packet
                        await asyncio.sleep(0.05)
                    result = await future
                    yield "event: packet\ndata: " + json.dumps(result, ensure_ascii=True) + "\n\n"
                except Cancelled:
                    yield "event: cancelled\ndata: {}\n\n"
                except Exception:  # Streamed failures must not echo captured text.
                    logging.getLogger("tompathy_engine").exception("History/reading analysis failed")
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
