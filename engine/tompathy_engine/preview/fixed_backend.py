"""Original Sounding Line fixed-Qwen wire identity, for a dedicated CPU service.

No service is started, stopped, downloaded, or borrowed here. The configured
loopback service must belong to this ToMpathy session. Foreign residency refuses.
"""

import asyncio
import logging
import math
from contextlib import contextmanager
from urllib.parse import urlsplit

import httpx

MODEL = "qwen3.5:9b"
DIGEST = "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7"
RUNTIME = "0.40.3"
OPTIONS = {"temperature": 0, "seed": 0, "num_predict": 256, "num_gpu": 0, "num_thread": 1, "num_ctx": 8192}


class FixedQwen:
    def __init__(self, url, *, timeout=110):
        parsed = urlsplit(url)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.path not in ("", "/") or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Dedicated Qwen service must be a loopback HTTP origin")
        self.url = url.rstrip("/")
        if not 5 <= timeout <= 600:
            raise ValueError("Dedicated Qwen transport timeout must be 5–600 seconds")
        self.timeout = timeout
        self.model_digest = DIGEST
        self.model_id = MODEL + "@" + DIGEST
        self.settings = dict(OPTIONS, runtime=RUNTIME, think=False, transport="s15-fixed-models-v1", context_guard="chars3-and-prompt-count-v1", keep_alive=120)
        self.owned = False
        self.uncertain = False
        self.check = lambda: None
        self.metrics = {"calls": 0, "loadMs": 0.0, "promptMs": 0.0, "generationMs": 0.0, "inputTokens": 0, "outputTokens": 0}

    @contextmanager
    def checking(self, check):
        previous, self.check = self.check, check
        try:
            yield
        finally:
            self.check = previous

    async def generate(self, payload):
        # Cancellation closes the HTTP connection. Recovery must verify that the
        # owned model unloaded before this backend may accept another call.
        async with httpx.AsyncClient(timeout=self.timeout, trust_env=False, follow_redirects=False) as client:
            task = asyncio.create_task(client.post(self.url + "/api/generate", json=payload))
            try:
                while not task.done():
                    self.check()
                    await asyncio.wait({task}, timeout=.1)
                self.check()
                return await task
            finally:
                if not task.done():
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)

    def inspect(self, client):
        version = client.get(self.url + "/api/version")
        version.raise_for_status()
        if version.json()["version"] != RUNTIME:
            raise ValueError("Fixed-Qwen runtime differs from its constructed test")
        tags = client.get(self.url + "/api/tags")
        tags.raise_for_status()
        if len([m for m in tags.json()["models"] if m["name"] == MODEL and m["digest"] == DIGEST]) != 1:
            raise ValueError("Fixed-Qwen model digest differs from its constructed test")
        response = client.get(self.url + "/api/ps")
        response.raise_for_status()
        residents = response.json()["models"]
        if residents and (not self.owned or len(residents) != 1 or residents[0]["digest"] != DIGEST or residents[0].get("size_vram") != 0 or residents[0].get("context_length") != 8192):
            raise RuntimeError("Dedicated service has foreign or non-CPU residency")
        return residents

    def complete(self, prompt, schema):
        self.check()
        if math.ceil(len(prompt) / 3) + OPTIONS["num_predict"] > OPTIONS["num_ctx"]:
            raise ValueError("Prompt may exceed the fixed reader's context window")
        if self.uncertain:
            raise RuntimeError("Previous Qwen completion is uncertain; restart the owned service")
        with httpx.Client(timeout=5, trust_env=False, follow_redirects=False) as client:
            self.inspect(client)
            self.uncertain = True
            self.owned = True
            try:
                response = asyncio.run(self.generate({"model": MODEL, "prompt": prompt,
                                      "format": schema, "stream": False, "keep_alive": 120, "options": OPTIONS, "think": False}))
            except BaseException:
                # Only this dedicated backend's exact model is eligible. A failed
                # unload keeps the backend blocked instead of assuming it stopped.
                try:
                    self.close(recover=True)
                except (httpx.HTTPError, ValueError, RuntimeError, KeyError):
                    logging.getLogger(__name__).warning("Owned reader recovery could not verify unload; backend remains blocked")
                raise
            response.raise_for_status()
            raw = response.json()
            self.owned = True
            if not self.inspect(client) or not raw.get("done"):
                raise RuntimeError("Fixed-Qwen completion or residency is unknown")
            self.uncertain = False
            if raw.get("prompt_eval_count", OPTIONS["num_ctx"]) + OPTIONS["num_predict"] >= OPTIONS["num_ctx"]:
                raise ValueError("Prompt filled the context window; refuse a potentially truncated answer")
            if raw.get("done_reason") != "stop" or raw.get("thinking"):
                raise ValueError("Fixed-Qwen response is unfinished or unexpectedly includes thinking")
            self.metrics["calls"] += 1
            for source, target, divisor in (("load_duration", "loadMs", 1e6), ("prompt_eval_duration", "promptMs", 1e6), ("eval_duration", "generationMs", 1e6), ("prompt_eval_count", "inputTokens", 1), ("eval_count", "outputTokens", 1)):
                value = raw.get(source)
                if isinstance(value, (int, float)) and math.isfinite(value) and value >= 0:
                    self.metrics[target] += value / divisor
            return {"text": raw["response"], "logprobs": None}

    def close(self, recover=False):
        if not self.owned or self.uncertain and not recover:
            return
        with httpx.Client(timeout=5, trust_env=False, follow_redirects=False) as client:
            if self.inspect(client):
                response = client.post(self.url + "/api/generate", json={"model": MODEL, "keep_alive": 0})
                response.raise_for_status()
                if self.inspect(client):
                    raise RuntimeError("Owned Qwen reader did not unload")
            self.owned = False
            self.uncertain = False
