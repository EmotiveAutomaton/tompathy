"""Evidence structure for the three views; never turns preview themes into drives."""
from datetime import datetime
from itertools import combinations
from typing import Literal

from pydantic import Field, model_validator

from ..ledger.ids import digest
from ..ledger.schema import Model

FIRST_MISSING = "No admitted comparison fit with conditional covariance."


class ViewRow(Model):
    id: str = Field(min_length=1, max_length=200)
    label: str = Field(min_length=1, max_length=300)
    order: int = Field(ge=0)
    date: str | None
    evidence: list[str] = Field(max_length=30)
    region: str | None = None


class ViewTip(Model):
    id: str = Field(min_length=1, max_length=200)
    label: str = Field(min_length=1, max_length=200)
    status: Literal["drawn", "named-not-drawn", "no-evidence", "no-admitted-reader"]
    support: float | None = Field(allow_inf_nan=False)
    interval: tuple[float, float] | None = None
    hypothesis: str | None = None


class ViewFeed(Model):
    row: str
    tip: str
    weight: float = Field(ge=0, le=1)


class CoSupport(Model):
    tips: tuple[str, str]
    share: float = Field(ge=0, le=1)


class WorkValueView(Model):
    work: str
    evidenceTier: Literal["T0", "production"]
    provenance: Literal["structure-only", "admitted"]
    asOf: str
    firstMissingLink: str | None
    rows: list[ViewRow] = Field(max_length=1500)
    tips: list[ViewTip] = Field(max_length=1000)
    feeds: list[ViewFeed] = Field(max_length=30000)
    coSupport: list[CoSupport] = Field(max_length=500)

    @model_validator(mode="after")
    def references(self):
        rows, tips = {r.id for r in self.rows}, {t.id for t in self.tips}
        if len(rows) != len(self.rows) or len(tips) != len(self.tips):
            raise ValueError("Duplicate value-view identity")
        drawn = {t.id for t in self.tips if t.status == "drawn"}
        for tip in self.tips:
            if tip.support is not None and (tip.interval is None or not tip.interval[0] <= tip.support <= tip.interval[1]):
                raise ValueError("Tip interval must contain its contrast")
            if tip.status in {"drawn", "named-not-drawn"} and (tip.support is None or not tip.hypothesis):
                raise ValueError("Estimated tips require their admitted hypothesis")
            if tip.status == "drawn" and tip.interval[0] <= 0:
                raise ValueError("Drawn tip requires lower 95% bound above zero")
        if (self.evidenceTier == "T0" or self.provenance == "structure-only") and any(t.support is not None or t.status in {"drawn", "named-not-drawn"} for t in self.tips):
            raise ValueError("Structure-only views cannot carry inferred tips")
        if any(f.row not in rows or f.tip not in tips for f in self.feeds):
            raise ValueError("Unresolved value-view feed")
        if any(a == b or a not in drawn or b not in drawn for a, b in (c.tips for c in self.coSupport)):
            raise ValueError("Co-support only connects distinct drawn tips")
        return self


def build_value_view(packet, *, tier=None, history=None):
    preview = packet["provider"].get("mode") == "preview"
    production = tier is not None and tier != "T0" or bool(history)
    evidence = {e["id"]: e for e in packet["evidence"]}
    events = [h for h in packet["hypotheses"] if h.get("interpretation") == "historical-event"]
    rows = [{"id": h["id"], "label": h["label"], "order": i,
             "date": next((evidence[e]["capturedAt"] for e in h["evidence"] if e in evidence), None),
             "evidence": h["evidence"], "region": None} for i, h in enumerate(events)]
    if history and not rows:
        rows = [{"id": digest(["view-revision", r.get("id"), r["t"], i]), "label": "Recorded revision",
                 "order": i, "date": datetime.fromisoformat(r["t"]).isoformat().replace("+00:00", "Z"), "evidence": [], "region": None}
                for i, r in enumerate(history.get("revisions", [])[:1500])]
    if not rows:
        rows = [{"id": r["id"], "label": r["anchor"]["exact"][:300], "order": i,
                 "date": None, "evidence": [], "region": r["id"]} for i, r in enumerate(packet["artifact"]["regions"])]
    projections = [] if preview or not production else [h for h in packet["hypotheses"]
        if h.get("valueCategory") == "drive" and h.get("preferenceEstimate", {}).get("quantity") == "Revealed-theme contrast from population"]
    tips, feeds = [], []
    for hypothesis in projections:
        estimate = hypothesis["preferenceEstimate"]
        interval = estimate.get("interval")
        if not interval or interval["level"] != .95:
            continue
        tips.append({"id": hypothesis["id"], "label": hypothesis["label"], "hypothesis": hypothesis["id"],
                     "support": estimate["value"], "interval": [interval["lower"], interval["upper"]],
                     "status": "drawn" if interval["lower"] > 0 else "named-not-drawn"})
        for row in rows:
            if set(row["evidence"]) & set(hypothesis["evidence"]):
                feeds.append({"row": row["id"], "tip": hypothesis["id"], "weight": 1.0})
    drawn = {t["id"] for t in tips if t["status"] == "drawn"}
    co_support = []
    for a, b in combinations(sorted(drawn), 2):
        left = {f["row"] for f in feeds if f["tip"] == a}
        right = {f["row"] for f in feeds if f["tip"] == b}
        if left | right:
            co_support.append({"tips": [a, b], "share": len(left & right) / len(left | right)})
    return {"work": packet["artifact"]["id"], "evidenceTier": "production" if production else "T0",
            "provenance": "admitted" if tips else "structure-only", "asOf": packet["artifact"]["capturedAt"],
            "firstMissingLink": None if tips else FIRST_MISSING if production else "Final text only — no recorded choices or revisions.",
            "rows": rows, "tips": tips, "feeds": feeds, "coSupport": co_support}
