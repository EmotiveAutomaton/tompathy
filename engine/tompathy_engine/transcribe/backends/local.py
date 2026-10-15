"""Opt-in local transports. No downloads, paid endpoints, or implicit GPU use."""

import os
import uuid
from contextlib import contextmanager
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
    def __init__(self, *, url, model, model_digest, protocol="ollama", gpu=False, gpu_lock=None):
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
        self.url, self.model, self.model_id = url.rstrip("/"), model, f"{model}@{model_digest}"
        self.model_digest, self.protocol, self.gpu, self.gpu_lock = (
            model_digest,
            protocol,
            gpu,
            gpu_lock,
        )
        self.settings = {"temperature": 0, "seed": 0, "protocol": protocol, "gpu": gpu}

    def complete(self, prompt, schema):
        if self.gpu:
            with gpu_lease(self.gpu_lock):
                return self._call(prompt, schema)
        return self._call(prompt, schema)

    def _call(self, prompt, schema):
        with httpx.Client(timeout=60, trust_env=False, follow_redirects=False) as client:
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
                resident = client.get(self.url + "/api/ps")
                resident.raise_for_status()
                if resident.json().get("models"):
                    raise RuntimeError(
                        "Local model service is already occupied; ToMpathy will not evict it"
                    )
                response = client.post(
                    self.url + "/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "format": schema,
                        "stream": False,
                        "keep_alive": 0,
                        "options": {
                            "temperature": 0,
                            "seed": 0,
                            "num_predict": 256,
                            "num_gpu": -1 if self.gpu else 0,
                            "num_thread": 1,
                        },
                    },
                )
                response.raise_for_status()
                value = response.json()
                if not value.get("done"):
                    raise RuntimeError("Local inference completion is unknown")
                resident = client.get(self.url + "/api/ps")
                resident.raise_for_status()
                if resident.json().get("models"):
                    raise RuntimeError(
                        "Model remains resident; retain the GPU lease for inspection"
                    )
                return {"text": value["response"], "logprobs": value.get("logprobs")}
            # Caller must run these dedicated servers CPU-only and pin their
            # model file. No API claim can authenticate arbitrary remote weights.
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
            value = response.json()["choices"][0]
            return {"text": value["message"]["content"], "logprobs": value.get("logprobs")}
