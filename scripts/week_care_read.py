"""TP56. Within-writer closeness slopes with a separate level for each news article."""

import csv
import json
import re
from pathlib import Path

import numpy as np
from cb_inputs import digest, pin
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import lsmr
from tompathy_engine.eval.readers.person_halves import summary
from tompathy_engine.eval.readers.tp31_teacher import sentences, valid_label
from tompathy_engine.eval.readers.word_panels import pinned

ROOT = Path(".local/week-20261122")
ESSAYS = Path(".local/readers/data/empathic-reactions/data/responses/data/messages.csv")
SOURCE = "380d2670254565629f81616df57cc0729de96ac87c056d05e39c370624ae8f64"
PRONOUNS = {"i", "me", "my"}


def indicators(writer, article):
    rows = np.arange(len(writer))
    columns = np.r_[writer, article + max(writer) + 1]
    return csr_matrix((np.ones(len(columns)), (np.tile(rows, 2), columns)))


def slopes(design, predictors, outcomes, counts):
    n = counts.sum()
    unavailable = np.full(3, np.nan)
    means = counts @ predictors / n
    scales = np.sqrt(counts @ ((predictors - means) ** 2) / n)
    if min(scales) <= 0:
        return unavailable
    root_weight = np.sqrt(counts)
    x = ((predictors - means) / scales).mean(1) * root_weight
    d = design.multiply(root_weight[:, None]).tocsr()
    fit = lsmr(d, x, atol=1e-11, btol=1e-11)
    if fit[1] not in (0, 1, 2, 4, 5):
        raise ValueError("Article and writer adjustment did not converge")
    residual = x - d @ fit[0]
    denominator = residual @ residual
    if denominator <= 1e-12 * n:
        return unavailable
    effects = (residual * root_weight) @ outcomes / denominator
    return np.r_[effects, effects[1] - effects[0]]


def prepare(out, check):
    audit = json.loads((ROOT / "Q22-transfer.json").read_bytes())
    mirror = Path(audit["mirror"])
    receipt = pinned(mirror / "receipt.json", audit["sourceReceiptPin"])
    if not (
        receipt["status"] == "complete"
        and audit["nativeExited"]
        and audit["priorFlockReleased"]
    ):
        raise ValueError("Q22 terminal verification required")
    prep = ROOT / "Q22-inputs-a"
    cfg = pinned(
        prep / "receipt.json",
        json.loads((prep / "complete.json").read_bytes())["sourceReceiptPin"],
    )
    if (
        pin(ESSAYS) != SOURCE
        or cfg["source"] != SOURCE
        or cfg["counts"]["articleTexts"] != 0
    ):
        raise ValueError(
            "Article-level fallback requires the verified public essay source"
        )
    items = pinned(prep / "spark-inputs/sentences.json", cfg["files"]["sentences.json"])
    binding = receipt["result"]["sentences"]["binding"]
    if (
        binding["inputPin"] != cfg["files"]["sentences.json"]
        or binding["role"] != "B"
        or binding["job"] != "Q22"
        or binding["block"] != "sentences"
    ):
        raise ValueError("Q22 sentence binding differs")
    data = []
    index = 0
    valid = 0
    with ESSAYS.open(encoding="utf-8-sig", newline="") as stream:
        for essay in csv.DictReader(stream):
            check()
            key = digest("Q22:" + essay["message_id"])
            own = []
            for j, text in enumerate(sentences(essay["essay"])):
                ident = digest(key + ":" + str(j))
                name = f"sentences/B/row-{index:06d}.json"
                row = pinned(mirror / name, audit["files"][name])
                if (
                    items[index] != {"id": ident, "text": text}
                    or row["id"] != ident
                    or row["index"] != index
                    or row["binding"] != binding
                ):
                    raise ValueError("Essay-to-sentence join differs")
                label = row["values"]
                if label is not None and valid_label(label) != label:
                    raise ValueError("Unexpected change mark")
                own.append(np.nan if label is None else int(label["whose"] == "writer"))
                valid += int(label is not None)
                index += 1
            words = re.findall(r"\b\w+\b", essay["essay"].casefold())
            if own and words and np.isfinite(own).all():
                data.append(
                    (
                        essay["response_id"],
                        essay["article_id"],
                        np.mean(own),
                        sum(w in PRONOUNS for w in words) / len(words),
                        float(essay["empathy"]),
                        float(essay["distress"]),
                    )
                )
    if index != len(items) or valid != receipt["result"]["sentences"]["valid"]:
        raise ValueError("Sentence coverage differs")
    result = {
        "card": "TP56",
        "source": audit["sourceReceiptPin"],
        "essaySource": SOURCE,
        "articleDropSlope": None,
        "dropByNeed": None,
        "essays": len(data),
        "excludedEssays": cfg["counts"]["essays"] - len(data),
        "validSentences": valid,
        "articleTexts": 0,
        "closeness": {},
    }
    if not data:
        return result
    writers, articles, own, pronouns, concern, distress = zip(*data, strict=True)
    w = np.unique(writers, return_inverse=True)[1]
    a = np.unique(articles, return_inverse=True)[1]
    d = indicators(w, a)
    x, y = np.column_stack((own, pronouns)), np.column_stack((concern, distress))
    point = slopes(d, x, y, np.ones(len(w)))
    for unit, group in (("writers", w), ("articles", a)):
        draws = []
        rng = np.random.default_rng(23)
        n = max(group) + 1
        for i in range(2000):
            if i % 10 == 0:
                check()
            counts = np.bincount(rng.integers(n, size=n), minlength=n)
            draws.append(slopes(d, x, y, counts[group]))
        result[unit] = int(n)
        for k, value, boot in zip(
            ("concern", "distress", "distressMinusConcern"),
            point,
            np.asarray(draws).T,
            strict=True,
        ):
            result["closeness"].setdefault(k, {})[unit] = summary(value, boot)
    for row in result["closeness"].values():
        if all(r["interval"] for r in row.values()):
            unit = max(row, key=lambda k: np.ptp(row[k]["interval"]))
            row["reportedUnit"] = unit
            row["reportedInterval"] = row[unit]["interval"]
    return result
