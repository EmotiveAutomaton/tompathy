"""Explicit anonymous download of the pinned Clef release; never executes it."""
import hashlib
import json
import urllib.request
from pathlib import Path

REVISION = "8b2e5fd17c09fd49bc2880b805d5323ec7ff4ff3"
ROOT = Path(__file__).resolve().parents[1] / ".local/clef-flash"
ROOT.mkdir(parents=True, exist_ok=True)
URL = "https://huggingface.co/Cloudflare/clef-flash"


def hashes(path):
    sha256 = hashlib.sha256()
    blob = hashlib.sha1(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            sha256.update(chunk)
            blob.update(chunk)
    return sha256.hexdigest(), blob.hexdigest()


def main():
    with urllib.request.urlopen(
        f"https://huggingface.co/api/models/Cloudflare/clef-flash/revision/{REVISION}?blobs=true", timeout=60
    ) as response:
        metadata = json.load(response)
    if metadata["sha"] != REVISION:
        raise ValueError("Model revision mismatch")
    (ROOT / "model-info.json").write_text(json.dumps(metadata, indent=2), encoding="utf8")
    files = {}
    for entry in sorted(metadata["siblings"], key=lambda item: item["rfilename"]):
        name = entry["rfilename"]
        if name == ".gitattributes":
            continue
        if Path(name).name != name:
            raise ValueError("Unexpected nested release file")
        target = ROOT / "model" / name
        target.parent.mkdir(exist_ok=True)
        expected = entry.get("lfs", {}).get("sha256") or entry["blobId"]
        if target.exists() and target.stat().st_size == entry["size"]:
            sha, blob = hashes(target)
            valid = (sha if entry.get("lfs") else blob) == expected
        else:
            valid = False
        if not valid:
            partial = target.with_suffix(target.suffix + ".partial")
            print(f"Downloading {name} ({entry['size'] / 1e9:.2f} GB)", flush=True)
            with urllib.request.urlopen(f"{URL}/resolve/{REVISION}/{name}", timeout=120) as response, partial.open("wb") as sink:
                while chunk := response.read(1024 * 1024):
                    sink.write(chunk)
            sha, blob = hashes(partial)
            if partial.stat().st_size != entry["size"] or (sha if entry.get("lfs") else blob) != expected:
                raise ValueError(f"Release checksum failed: {name}")
            partial.replace(target)
        files[name] = {"bytes": target.stat().st_size, "sha256": sha}
        print(f"Verified {name}", flush=True)
    manifest = {"model": "Cloudflare/clef-flash", "revision": REVISION, "files": files}
    # Keep the verified Windows release-manifest bytes reproducible on all hosts.
    (ROOT / "manifest.json").write_bytes((json.dumps(manifest, indent=2) + "\n").replace("\n", "\r\n").encode("utf8"))
    print("Pinned release fully verified", flush=True)


if __name__ == "__main__":
    main()
