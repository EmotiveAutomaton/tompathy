"""Explicit public GitHub file history; serial, quota-aware, bounded reads."""

import base64
import re
from urllib.parse import quote, unquote, urlsplit

import httpx

from .history import LICENSES


def trailers(message):
    """Only literal unsigned declarations create tool entries."""
    out = []
    for match in re.finditer(r"^Co-authored-by:\s*(.+?)\s*<([^<>\r\n]+)>\s*$", message, re.IGNORECASE | re.MULTILINE):
        label, email = match.groups()
        if re.fullmatch(r"Claude(?: (?:Opus|Sonnet|Haiku))?(?: [\d.]+)?|Copilot(?: coding agent)?|ChatGPT|OpenAI Codex|Codex|Gemini(?: [\d.]+)?", label, re.IGNORECASE) or email.lower() in {"noreply@anthropic.com", "copilot@github.com"}:
            out.append({"label": label[:250], "kind": "model", "detail": match.group().strip()[:1000]})
    for match in re.finditer(r"^(?:Made with Cursor|Cursor-Agent):?[^\r\n]*$", message, re.IGNORECASE | re.MULTILINE):
        out.append({"label": "Cursor", "kind": "tool", "detail": match.group().strip()[:1000]})
    return out


def fetch_history(url, *, artifact_id, limit=20, cancel=lambda: False, token=None, client=None):
    parsed = urlsplit(url)
    parts = parsed.path.strip("/").split("/")
    if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment or len(parts) < 5 or parts[2] != "blob" or not 1 <= limit <= 100:
        raise ValueError("Choose a public GitHub file URL with a single-component or encoded branch and 1–100 revisions")
    owner, repo, _, ref, *path = parts
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", v) and v not in {".", ".."} for v in (owner, repo)):
        raise ValueError("Invalid GitHub repository")
    file = unquote("/".join(path))
    if not file or ".." in file.split("/"):
        raise ValueError("Invalid GitHub file path")
    owned = client is None
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ToMpathyEngine/0.1 (local reading)", "X-GitHub-Api-Version": "2026-03-10"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    client = client or httpx.Client(timeout=15, follow_redirects=False, trust_env=False, headers=headers)
    base, remaining, total_bytes = f"https://api.github.com/repos/{owner}/{repo}", None, 0
    def get(path, params=None):
        nonlocal remaining, total_bytes
        if cancel():
            raise InterruptedError("GitHub history cancelled")
        if remaining is not None and remaining < 1:
            raise ValueError("GitHub quota exhausted; wait for reset or supply an optional token")
        response = client.get(base + path, params=params)
        remaining = int(response.headers["x-ratelimit-remaining"]) if response.headers.get("x-ratelimit-remaining", "").isdigit() else remaining
        response.raise_for_status()
        if len(response.content) > 4_000_000:
            raise ValueError("GitHub response exceeds the history bound")
        total_bytes += len(response.content)
        if total_bytes > 32_000_000:
            raise ValueError("GitHub history exceeds the aggregate response bound")
        return response.json()
    try:
        repository = get("")
        if repository.get("private") is not False:
            raise ValueError("Only public GitHub history is accepted by this adapter")
        license_info = get("/license")
        license = license_info.get("license", {}).get("spdx_id")
        if license not in LICENSES:
            raise ValueError("GitHub history lacks an allowlisted license witness")
        commits = get("/commits", {"path": file, "sha": unquote(ref), "per_page": limit})
        if not isinstance(commits, list) or not commits or len(commits) > limit:
            raise ValueError("No bounded GitHub file history was returned")
        snapshots, texts = [], {}
        def text_at(sha, allow_absent=False):
            if sha in texts:
                return texts[sha]
            try:
                content = get("/contents/" + quote(file, safe="/"), {"ref": sha})
            except httpx.HTTPStatusError as error:
                if allow_absent and error.response.status_code == 404:
                    return ""  # Witnessed absence in the actual tree parent.
                raise
            if content.get("encoding") != "base64" or content.get("size", 4_000_001) > 1_000_000:
                raise ValueError("GitHub file exceeds the text snapshot bound")
            text = base64.b64decode(content["content"]).decode("utf8")
            if "\0" in text:
                raise ValueError("GitHub file is not readable text")
            texts[sha] = text
            return text
        for row in reversed(commits):
            sha = row["sha"]
            if not re.fullmatch(r"[a-f0-9]{40}", sha):
                raise ValueError("Invalid GitHub commit pin")
            text = text_at(sha)
            parents = [p["sha"] for p in row.get("parents", [])]
            if any(not re.fullmatch(r"[a-f0-9]{40}", parent) for parent in parents):
                raise ValueError("Invalid GitHub parent pin")
            witness = {"revision": parents[0], "text": text_at(parents[0], allow_absent=True)} if len(parents) == 1 else None
            metadata = row["commit"]
            author = metadata["author"]
            declared = trailers(metadata["message"])
            if author["name"].lower().endswith("(aider)"):
                declared.append({"label": "Aider", "kind": "tool", "detail": "Declared author suffix: " + author["name"]})
            snapshots.append({"id": sha, "parents": parents,
                              "maker": str(row.get("author", {}).get("id")) if row.get("author") else author["email"],
                              "label": author["name"], "t": metadata["committer"]["date"], "summary": metadata["message"],
                              "text": text, "declared_tools": declared, **({"parent_text_witness": witness} if witness else {})})
        return {"artifact_id": artifact_id, "source_uri": url, "license": license,
                "license_evidence": license_info.get("html_url", base + "/license"), "revisions": snapshots,
                "quotaRemaining": remaining, "file": file,
                "declaredAiCommitShare": sum(bool(r["declared_tools"]) for r in snapshots) / len(snapshots)}
    finally:
        if owned:
            client.close()
