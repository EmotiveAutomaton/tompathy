"""Serial source metadata/reachability audit, not automatic claim validation."""
import html
import json
from pathlib import Path
import re
import time
from datetime import UTC, datetime
import httpx
import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=Path("docs/citation-url-audit-2026-10-17.json"))
parser.add_argument("--abstracts", type=Path, help="Optional local review notes; do not publish retrieved abstracts")
args = parser.parse_args()
root = Path("docs/website-essay-handoff")
references = json.loads((root / "content.json").read_text(encoding="utf8"))["bibliography"]
rows = []
abstracts = {}
with httpx.Client(timeout=8, follow_redirects=True, headers={"User-Agent": "ToMpathy-reference-audit/1.0"}) as client:
    for ref in references:
        row = dict(ref)
        url = ref["href"]
        try:
            if url.startswith("https://doi.org/10."):
                response = client.get("https://api.crossref.org/works/" + url.removeprefix("https://doi.org/"))
                row["metadataStatus"] = response.status_code
                if response.is_success:
                    meta = response.json()["message"]
                    if meta.get("abstract"):
                        abstracts[url] = re.sub(r"<[^>]+>", " ", html.unescape(meta["abstract"]))
                    row.update(registeredTitle=meta.get("title"), registeredAuthors=meta.get("author"),
                               registeredPublication=meta.get("container-title"), registeredDate=meta.get("published"),
                               registeredURL=meta.get("URL"), destination=meta.get("resource", {}).get("primary", {}).get("URL"),
                               result="DOI registration verified; destination/claim not automatically validated")
                else:
                    row["result"] = "DOI metadata unresolved"
            else:
                with client.stream("GET", url) as response:
                    row.update(httpStatus=response.status_code, destination=str(response.url))
                    body = b""
                    for chunk in response.iter_bytes():
                        body += chunk
                        if len(body) >= 300_000: break
                    title = re.search(r"<title[^>]*>(.*?)</title>", body.decode("utf8", errors="replace"), re.S | re.I)
                    if title: row["pageTitle"] = html.unescape(re.sub(r"\s+", " ", title[1])).strip()
                    row["result"] = (
                        "HTTP 202 response; content access unconfirmed" if response.status_code == 202
                        else "reachable; claim not automatically validated" if response.is_success
                        else "destination unresolved (may be access restriction)"
                    )
        except Exception as exc:
            row["result"] = "request unresolved"
            row["error"] = type(exc).__name__
        rows.append(row)
        args.output.write_text(json.dumps({"checkedAt": datetime.now(UTC).isoformat(), "rows": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
        if args.abstracts:
            args.abstracts.write_text(json.dumps(abstracts, indent=2, ensure_ascii=False), encoding="utf8")
        print(f'{len(rows)}/{len(references)} {row["result"]}', flush=True)
        time.sleep(.15)
