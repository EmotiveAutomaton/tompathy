"""Refusal stability and cross-prompt session matching on the public CoAuthor census."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from ...adapters.replay import replay
from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .tp23 import saved_vectors

ROSTER = "b6527b4c90cc830383f6c7562c7e24dd99c327581350603e144c202e9292a8d1"
ENCODER = "e1d74ca91f391fa702a0aa8c395761c260a3fccd928c2855e5cc20c35f8e22b1"
LIMIT = "Observed suggestions in public CoAuthor sessions. Person identification and channel inference are outside this study."


def opened(episode):
    if not episode["usable"] or not episode["options"]:
        return None
    offers = [opt["original"] for opt in episode["options"]]
    accepted = []
    if episode["decision"] in {"accept", "edit"}:
        actual = {opt["original"] for opt in episode["options"]
                  if opt["index"] in episode["matched_option_indices"]}
        if not episode["verified_insertion"] or len(actual) != 1:
            return None
        accepted = list(actual)
    return offers, offers if episode["decision"] == "dismiss" else [], accepted


def intake(config, output, check):
    settings = json.loads(Path(config).read_bytes())
    path = Path(settings["rawRoster"])
    if sha256(path) != ROSTER:
        raise ValueError("Public roster changed")
    root = Path(settings["rawRoot"]).resolve()
    allowed = (root / "corpora/coauthor").resolve()
    roster = json.loads(path.read_bytes())
    if len(roster) != 1445 or len({row["session"] for row in roster}) != len(roster):
        raise ValueError("Unexpected public session census")
    words, sessions, counts = {}, [], Counter()
    with (output / "opened.jsonl").open("x", encoding="utf8") as stream:
        for index, row in enumerate(roster):
            check()
            source = (root / row["path"]).resolve()
            if not source.is_relative_to(allowed) or sha256(source) != row["source_sha256"]:
                raise ValueError("Public session binding changed")
            if not row["reconstructed"]:
                counts["excludedSessions"] += 1
                continue
            with source.open(encoding="utf8") as handle:
                result = replay(line for line in handle if line.strip())
            if not result["reconstructed"]:
                counts["excludedSessions"] += 1
                continue
            ids = [[], [], []]
            menus = 0
            for event in result["events"]:
                groups = opened(event)
                if groups is None:
                    counts["excludedMenus"] += 1
                    continue
                menus += 1
                for group_ids, texts in zip(ids, groups, strict=True):
                    group_ids.extend(words.setdefault(t, len(words)) for t in texts)
            if menus:
                record = [row["session"], row["writer"], row["prompt"], menus, ids]
                sessions.append(record)
                stream.write(json.dumps(record) + "\n")
            else:
                counts["emptySessions"] += 1
            if index % 16 == 0:
                stream.flush()
                save_json(output / "progress.json", {"phase":"replay", "sessions":index + 1, "total":len(roster)})
    save_json(output / "unique-texts.json", list(words))
    return sessions, list(words), dict(counts)


def unit(vector):
    norm = np.linalg.norm(vector)
    return vector / norm if norm > 1e-10 else None


def session_totals(sessions, vectors):
    dim = vectors.shape[1]
    sums = []
    centers = defaultdict(lambda: np.zeros(dim))
    n = Counter()
    for _, _, prompt, _, groups in sessions:
        values = np.array([vectors[group].sum(axis=0, dtype=np.float64) if group else np.zeros(dim)
                           for group in groups])
        centers[prompt] += values[0]
        n[prompt] += len(groups[0])
        sums.append(values)
    counts = np.array([[len(g) for g in row[4]] for row in sessions])
    for i, row in enumerate(sessions):
        sums[i] -= counts[i, :, None] * (centers[row[2]] / n[row[2]])
    return np.asarray(sums), counts, np.array([r[3] for r in sessions])


def profile(index, sums, counts, menus):
    total = sums[index].sum(0)
    num = counts[index].sum(0)
    mean = total / np.maximum(num[:, None], 1)
    refusal = unit(mean[1] - mean[0]) if num[1] else None
    accept = unit(mean[2] - mean[0]) if num[2] else None
    return refusal, accept, num[2] / menus[index].sum()


def match_credit(scores, true):
    tied = np.isclose(scores, np.min(scores), rtol=0, atol=1e-12)
    return float(tied[true]) / tied.sum()


def measure(sessions, sums, counts, menus, check):
    people = defaultdict(list)
    for i, (_, writer, *_) in enumerate(sessions):
        people[writer].append(i)
    halves, eligible = [], []
    for writer, ix in sorted(people.items()):
        ordered = sorted(ix, key=lambda i: hashlib.sha256(str(sessions[i][0]).encode()).digest())
        if len(ix) < 4:
            continue
        split = [ordered[::2], ordered[1::2]]
        if min(counts[j, 1].sum() for j in split) < 20:
            continue
        dirs = [profile(j, sums, counts, menus)[0] for j in split]
        if all(v is not None for v in dirs):
            eligible.append(writer)
            halves.append(dirs)
    result = {"eligibleWriters":len(eligible), "writerDraws":2000, "matching":None, "stability":None}
    if len(eligible) < 2:
        return result, {}
    pairs = np.array(halves)
    matrix = pairs[:, 0] @ pairs[:, 1].T
    nw = len(eligible)
    rng = np.random.default_rng(32)
    weights = rng.multinomial(nw, np.full(nw, 1 / nw), size=2000)
    def gap(w):
        d = np.diag(matrix)
        off = w.sum() ** 2 - w @ w
        return (w @ d / w.sum() - (w @ matrix @ w - w**2 @ d) / off) if off else np.nan
    draws = np.array([gap(w) for w in weights])
    bounds = np.quantile(draws[np.isfinite(draws)], [.025, .975]).tolist()
    result["stability"] = {"gain":gap(np.ones(nw)), "interval":bounds, "passes":bool(bounds[0] > 0),
                           "finiteDraws":int(np.isfinite(draws).sum())}
    tally = np.zeros((nw, 3))
    forecast = []
    for prompt in sorted({row[2] for row in sessions}):
        check()
        refs = {}
        for w, writer in enumerate(eligible):
            ix = [i for i in people[writer] if sessions[i][2] != prompt]
            if ix:
                r, a, rate = profile(ix, sums, counts, menus)
                if r is not None and a is not None:
                    refs[w] = (r, a, rate)
        if len(refs) < 2:
            continue
        rr, aa, rates = (np.asarray(v) for v in zip(*refs.values(), strict=True))
        for true, w in enumerate(refs):
            for i in people[eligible[w]]:
                if sessions[i][2] != prompt:
                    continue
                r, a, rate = profile([i], sums, counts, menus)
                if r is None or a is None:
                    continue
                base_sum = (1 - aa @ a) / 2 + abs(rates - rate)
                base = match_credit(base_sum / 2, true)
                extra = match_credit((base_sum + (1 - rr @ r) / 2) / 3, true)
                tally[w] += [1, base, extra]
                forecast.append([i, w, len(refs), base, extra])
    nt, base, aug = tally.sum(0)
    if nt:
        boot = weights @ tally
        ok = boot[:, 0] > 0
        diff = (boot[ok, 2] - boot[ok, 1]) / boot[ok, 0]
        gain = (aug - base) / nt
        result["matching"] = {"sessions":int(nt), "writers":int(np.count_nonzero(tally[:, 0])),
            "baseline":base / nt, "augmented":aug / nt, "gain":gain, "passes":bool(gain >= .03),
            "interval":np.quantile(diff, [.025, .975]).tolist(), "finiteDraws":int(ok.sum())}
    return result, {"cosines":matrix, "writerTotals":tally, "queries":np.asarray(forecast)}


def run(config, models, output, check, ledger, protocol):
    if sha256(models / "minilm/intake.json") != ENCODER:
        raise ValueError("Frozen MiniLM identity changed")
    provenance = {"card":"TP32", "ledger":ledger, "protocolPin":sha256(protocol),
                  "rosterPin":ROSTER, "encoderPin":ENCODER, "productionAdmission":False, "scope":LIMIT}
    save_json(output / "receipt.json", {**provenance, "status":"running"})
    sessions, texts, missing = intake(config, output, check)
    save_json(output / "progress.json", {"phase":"encoding", "uniqueTexts":len(texts)})
    vectors, _ = saved_vectors(texts, models, output / "vectors", check)
    sums, counts, menus = session_totals(sessions, vectors)
    np.savez(output / "sessions.npz", sums=sums, counts=counts, menus=menus)
    result, archive = measure(sessions, sums, counts, menus, check)
    np.savez(output / "comparisons.npz", **archive)
    save_json(output / "receipt.json", {**provenance, **result, "status":"complete",
        "intake":{"sessions":len(sessions), "writers":len({r[1] for r in sessions}), "uniqueSuggestions":len(texts),
                  "menus":int(menus.sum()), "offeredDismissedAccepted":counts.sum(0).tolist(), **missing},
        "archivePins":{name:sha256(output / name) for name in
                       ("sessions.npz", "opened.jsonl", "unique-texts.json", "comparisons.npz")}})
