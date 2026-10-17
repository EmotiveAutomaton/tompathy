"""Opt-in local transports. No downloads, paid endpoints, or implicit GPU use."""

import hashlib
import math
import os
import tempfile
import uuid
from contextlib import ExitStack, contextmanager
from pathlib import Path
from urllib.parse import urlsplit

import httpx


@contextmanager
def gpu_lease(path):
    """Sounding Line compatible PID/tag lock; unknown completion retains ownership."""
    if path is None:
        raise ValueError("GPU calls require the shared research GPU lock path")
    path = Path(path)
    token = f"{os.getpid()} tompathy:{uuid.uuid4().hex}".encode()
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(fd, token)
    finally:
        os.close(fd)
    finished = False
    try:
        yield
        finished = True
    finally:
        # Never reclaim someone else's lock or release after an uncertain call.
        if finished and path.exists() and path.read_bytes() == token:
            path.unlink()


class LocalBackend:
    def __init__(self, *, url, model, model_digest, protocol="ollama", gpu=False, gpu_lock=None,
                 keep_alive=120, num_thread=1, num_ctx=8192, timeout=600):
        parsed = urlsplit(url)
        if (
            parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in ("", "/")
        ):
            raise ValueError("Transcriber endpoints must be explicit loopback HTTP origins")
        if protocol not in {"ollama", "llamacpp", "openai_compat"} or not model_digest:
            raise ValueError("Choose a supported local protocol and immutable model pin")
        if gpu and protocol != "ollama":
            raise ValueError(
                "GPU residency verification currently supports only Ollama; use a CPU server for this protocol"
            )
        if not isinstance(keep_alive, int) or not 0 <= keep_alive <= 3600:
            raise ValueError("keep_alive must be 0–3600 seconds")
        if num_thread not in (1, 2) or not isinstance(num_ctx, int) or not 512 <= num_ctx <= 131072:
            raise ValueError("Use 1–2 CPU threads and an explicit 512–131072 token context")
        if not 5 <= timeout <= 600:
            raise ValueError("Transport timeout must be 5–600 seconds")
        self.url, self.model, self.model_id = url.rstrip("/"), model, f"{model}@{model_digest}"
        self.model_digest, self.protocol, self.gpu, self.gpu_lock = (
            model_digest,
            protocol,
            gpu,
            gpu_lock,
        )
        self.settings = {"temperature": 0, "seed": 0, "protocol": protocol, "gpu": gpu,
                         "keep_alive": keep_alive, "num_thread": num_thread, "num_ctx": num_ctx,
                         "num_predict": 256, "context_guard": "chars-div-3-or-tokenizer-v1"}
        self.timeout = timeout
        self._session = False
        self._owned = False
        endpoint = hashlib.sha256(self.url.encode()).hexdigest()[:24]
        self._lock = Path(tempfile.gettempdir()) / f"tompathy-ollama-{endpoint}.lock"

    def _residents(self, client):
        response = client.get(self.url + "/api/ps")
        response.raise_for_status()
        payload = response.json()
        residents = payload.get("models") if isinstance(payload, dict) else None
        if not isinstance(residents, list) or any(not isinstance(m, dict) for m in residents):
            raise RuntimeError("Local model residency is unknown; retain any active lease")
        if residents and (not self._owned or any(
            m.get("name", m.get("model")) != self.model or m.get("digest") != self.model_digest
            or (not self.gpu and m.get("size_vram") != 0) for m in residents
        )):
            raise RuntimeError("Local model service has unowned residency; ToMpathy will not evict it")
        return residents

    @contextmanager
    def session(self):
        """Own the endpoint and (when requested) GPU until verified unload.

        A nested transcription borrows this same lease. Matching residency at
        entry is still foreign: model identity alone does not confer ownership.
        """
        if self._session or self.protocol != "ollama":
            yield self
            return
        failure = None
        with ExitStack() as stack:
            stack.enter_context(gpu_lease(self._lock))
            if self.gpu:
                stack.enter_context(gpu_lease(self.gpu_lock))
            self._session = True
            try:
                try:
                    with httpx.Client(timeout=5, trust_env=False) as client:
                        self._residents(client)
                    yield self
                except BaseException as exc:  # noqa: BLE001 — defer even cancellation until owned-model cleanup
                    failure = exc
                finally:
                    if self._owned:
                        with httpx.Client(timeout=self.timeout, trust_env=False) as client:
                            if self._residents(client):
                                response = client.post(self.url + "/api/generate", json={"model": self.model, "keep_alive": 0})
                                response.raise_for_status()
                            if self._residents(client):
                                raise RuntimeError("Owned model unload is unverified; retain lease for inspection")
                            self._owned = False
            finally:
                self._session = False
        # Verified unload releases the lease even when a request was rejected.
        if failure is not None:
            raise failure

    def complete(self, prompt, schema):
        # Check before taking a lock or loading a model.
        if self.protocol != "llamacpp" and math.ceil(len(prompt) / 3) + 256 > self.settings["num_ctx"]:
            raise ValueError("Prompt may exceed the configured context window; shorten the input")
        with self.session():
            return self._call(prompt, schema)

    def _call(self, prompt, schema):
        with httpx.Client(timeout=self.timeout, trust_env=False, follow_redirects=False) as client:
            if self.protocol == "ollama":
                tags = client.get(self.url + "/api/tags")
                tags.raise_for_status()
                found = [
                    m
                    for m in tags.json()["models"]
                    if m["name"] == self.model and m["digest"] == self.model_digest
                ]
                if len(found) != 1:
                    raise ValueError("Installed model does not match transcriber pin")
                self._residents(client)
                self._owned = True
                response = client.post(
                    self.url + "/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "format": schema,
                        "stream": False,
                        "keep_alive": self.settings["keep_alive"],
                        "options": {
                            "temperature": 0,
                            "seed": 0,
                            "num_predict": 256,
                            "num_gpu": -1 if self.gpu else 0,
                            "num_thread": self.settings["num_thread"],
                            "num_ctx": self.settings["num_ctx"],
                        },
                    },
                )
                response.raise_for_status()
                value = response.json()
                if not value.get("done"):
                    raise RuntimeError("Local inference completion is unknown")
                self._residents(client)
                if value.get("prompt_eval_count", self.settings["num_ctx"]) + 256 >= self.settings["num_ctx"]:
                    raise ValueError("Prompt filled the context window; refuse a potentially truncated answer")
                return {"text": value["response"], "logprobs": value.get("logprobs")}
            # Caller must run these dedicated servers CPU-only and pin their
            # model file. No API claim can authenticate arbitrary remote weights.
            if self.protocol == "llamacpp":
                tokens = client.post(self.url + "/tokenize", json={"content": prompt, "add_special": True})
                tokens.raise_for_status()
                if len(tokens.json()["tokens"]) + 256 > self.settings["num_ctx"]:
                    raise ValueError("Prompt exceeds the configured context window")
            body = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "seed": 0,
                "max_tokens": 256,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": "literal", "strict": True, "schema": schema},
                },
            }
            response = client.post(self.url + "/v1/chat/completions", json=body)
            response.raise_for_status()
            raw = response.json()
            if raw.get("usage", {}).get("prompt_tokens", self.settings["num_ctx"]) + 256 >= self.settings["num_ctx"]:
                raise ValueError("Prompt filled the context window or token usage is unavailable")
            value = raw["choices"][0]
            return {"text": value["message"]["content"], "logprobs": value.get("logprobs")}
