"""Local reader payoff probes with explicit repetition and shuffle controls."""

import random
from statistics import mean
from time import monotonic

import numpy as np

from ..adapters.capture import utf16_length
from ..ledger.ids import digest
from .surface import SENTENCE, source_holdouts, words


def payoff_steps(packet, reader, check, publish):
    from .build import LABELS, hypothesis, partition_attention, relative

    regions = packet["artifact"]["regions"]
    sentences = [(r, s) for r in regions for s in SENTENCE.finditer(r["anchor"]["exact"])]
    summary = (packet["artifact"]["title"] + " " + packet["artifact"].get("metaDescription", ""))[:1000]
    texts = [s.group() for _, s in sentences]
    seen, tail_ids, prefix, rows, contextless = set(), [], "", [], []
    started = monotonic()
    from .judgments import advance
    # Layer 2 adds two matched conditions per earlier-paragraph window.
    layer2 = sum(2 * i for i, r in enumerate(regions) if len(list(SENTENCE.finditer(r["anchor"]["exact"]))) >= 2) if len(regions) <= 20 else 0
    total, completed = 4 * len(sentences) + layer2, 0
    advance(packet, "payoff", 0, total, "score calls")

    def losses(text, context):
        return reader.score(text, context, check)

    def average(text, tokens, blocked=(), code=()):
        selected = [w["nats"] for w in words(text, tokens, code) if w["content"] and not w["held"] and not any(w["start"] < b and w["end"] > a for a, b in blocked)]
        return mean(selected) if selected else None

    emitted = set()
    def flush_layer1():
        packet["hypotheses"] = [h for h in packet["hypotheses"] if h["id"] not in emitted]
        for frame in packet.get("currentAttention", []):
            frame["items"] = [i for i in frame["items"] if i["hypothesis"] not in emitted]
        packet["currentAttention"] = [f for f in packet.get("currentAttention", []) if f["items"]]
        emitted.clear()
        if not rows:
            raise ValueError("No payoff sentences survive the surface holdouts")
        count = max(1, int(np.ceil(len(rows) * .1)))
        top = sorted(rows, key=lambda r: -r["gain"])[:count]
        novel_top = sorted([r for r in rows if r["novelGain"] is not None], key=lambda r: -r["novelGain"])[:count]
        retained = len({(r["region"], r["start"]) for r in top} & {(r["region"], r["start"]) for r in novel_top}) / count
        common = f"Reader {reader.identity['id']} at {reader.identity['revision']}, manifest SHA-256 {reader.identity['sha256']}. Proxies for what the author set up; not measured enjoyment."
        scale = (min(-1, *(r["gain"] for r in rows)), max(1, *(r["gain"] for r in rows)))
        for index, row in enumerate(top):
            span = {"region": row["region"], "start": row["start"], "end": row["end"]}
            score = relative(row["gain"], "Mean content-word surprisal with extractive summary minus prior page context, in nats; not probability.", scale)
            positive = row["gain"] > 0
            h = hypothesis(packet, ["payoff", row["region"], row["start"], row["end"]], ("Pays off: " if positive else "No positive payoff: ") + row["text"].strip(),
                           ("Earlier text lowered this sentence's loss. " if positive else "Even this top-ranked sentence has no positive gain from earlier text. ") + f"Gain {row['gain']:.3f} nats; shuffled-prior gain {row['shuffleGain']:.3f}; novel-span gain {row['novelGain'] if row['novelGain'] is not None else 'unavailable'}; novel shuffled-prior gain {row['novelShuffleGain'] if row['novelShuffleGain'] is not None else 'unavailable'}. Ordered and shuffled controls use matched context-token counts and the 2,048-token window. Short synopsis uses the title and available meta description, capped at 1,000 characters; its context is shorter. " + common,
                           kind="attention", regions=[row["region"]], support=score, spans=[span])
            emitted.add(h["id"])
            h["description"] += f" Scores cover {len(rows)} of {len(sentences)} sentences surviving holdouts so far; rankings may change."
            packet.setdefault("currentAttention", []).append({"maker": h["makers"][0], "span": span, "items": [{"hypothesis": h["id"], "support": score, **LABELS}]})
        partition_attention(packet)
        report = {"sentencesScored": len(rows), "totalSentences": len(sentences), "layer1NovelRetention": retained, "layer1Seconds": monotonic() - started,
                  "contextFreeMean": mean(contextless) if contextless else None,
                  "easyWithoutContext": bool(contextless and mean(contextless) < 2),
                  "layer2Status": "skipped: more than 20 paragraphs" if len(regions) > 20 else "pending"}
        packet["preview"]["payoff"] = report
        publish()
        return report

    for index, (region, sentence) in enumerate(sentences):
        check()
        text = sentence.group()
        encoding = reader.tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
        ids, offsets = encoding["input_ids"], encoding["offset_mapping"]
        repeated = []
        joined = tail_ids + ids
        for i in range(max(0, len(joined) - 3)):
            gram = tuple(joined[i:i + 4])
            if gram in seen:
                first, last = max(0, i - len(tail_ids)), i + 3 - len(tail_ids)
                if last >= 0:
                    repeated.append((offsets[first][0], offsets[last][1]))
            seen.add(gram)
        tail_ids = joined[-3:]
        # Match context length/position, excluding this exact target from controls.
        preceding = texts[:index]
        random.Random(digest(["payoff-shuffle-v2", packet["artifact"]["revision"], index])).shuffle(preceding)
        shuffled_before = " ".join(preceding)
        prefix_ids = reader.tokenizer.encode(prefix, add_special_tokens=False)[-2047:]
        shuffled_ids = reader.tokenizer.encode(shuffled_before, add_special_tokens=False)[-2047:]
        # Identical context token counts put the identical scored target at the
        # same position in the ordered and shuffled conditions.
        length = min(len(prefix_ids), len(shuffled_ids))
        prefix_ids, shuffled_ids = (prefix_ids[-length:], shuffled_ids[-length:]) if length else ([], [])
        short = losses(text, summary)
        completed += 1
        advance(packet, "payoff", completed, total, "score calls")
        publish()
        yield
        full = losses(text, prefix_ids)
        completed += 1
        advance(packet, "payoff", completed, total, "score calls")
        publish()
        yield
        control = losses(text, shuffled_ids)
        completed += 1
        advance(packet, "payoff", completed, total, "score calls")
        publish()
        yield
        empty = losses(text, "")
        completed += 1
        advance(packet, "payoff", completed, total, "score calls")
        if empty:
            contextless.extend(t["nats"] for t in empty)
        code = source_holdouts(region, sentence.start(), sentence.end())
        scores = [average(text, tokens, code=code) for tokens in (short, full, control)]
        novel = [average(text, tokens, repeated, code) for tokens in (short, full, control)]
        if all(v is not None for v in scores):
            rows.append({"region": region["id"], "text": text, "start": utf16_length(region["anchor"]["exact"][:sentence.start()]),
                         "end": utf16_length(region["anchor"]["exact"][:sentence.end()]), "gain": scores[0] - scores[1],
                         "shuffleGain": scores[0] - scores[2], "novelGain": novel[0] - novel[1] if all(v is not None for v in novel) else None,
                         "novelShuffleGain": novel[0] - novel[2] if all(v is not None for v in novel) else None})
        prefix += " " + text
        if rows:
            flush_layer1()
        else:
            publish()
        yield
    report = flush_layer1()
    common = f"Reader {reader.identity['id']} at {reader.identity['revision']}. Not measured enjoyment."
    if len(regions) > 20 or "payoff-layer-2" in packet["preview"].get("budgetDrops", []):
        report["layer2Status"] = "omitted: page-size or live time budget; layer 1 retained"
        return
    # Fixed bounded earlier window per paragraph. Both conditions score the exact
    # same target at the same position; only the future paragraph order differs.
    late = []
    # Four-token strings in the ordered future paragraph are held out of the
    # earlier target as well: literal copying must not masquerade as a payoff.
    def copied_spans(text, future):
        encoding = reader.tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
        future_ids = reader.tokenizer.encode(future, add_special_tokens=False)
        grams = {tuple(future_ids[i:i + 4]) for i in range(max(0, len(future_ids) - 3))}
        ids, offsets = encoding["input_ids"], encoding["offset_mapping"]
        return [(offsets[i][0], offsets[i + 3][1]) for i in range(max(0, len(ids) - 3)) if tuple(ids[i:i + 4]) in grams]
    for index, region in enumerate(regions):
        check()
        if "payoff-layer-2" in packet["preview"].get("budgetDrops", []):
            report["layer2Status"] = "omitted at live time budget; layer 1 retained"
            return
        text = region["anchor"]["exact"]
        pieces = [s.group() for s in SENTENCE.finditer(text)]
        if index and len(pieces) >= 2:
            scrambled = pieces.copy()
            random.Random(digest(["payoff-spoiler-v1", text])).shuffle(scrambled)
            if scrambled == pieces:
                scrambled = list(reversed(pieces))
            ordered_ids = reader.tokenizer.encode(text, add_special_tokens=False)[-2047:]
            shuffled_ids = reader.tokenizer.encode(" ".join(scrambled), add_special_tokens=False)[-2047:]
            length = min(len(ordered_ids), len(shuffled_ids))
            ordered_ids, shuffled_ids = ordered_ids[-length:], shuffled_ids[-length:]
            windows = []
            for earlier in regions[:index]:
                check()
                target = earlier["anchor"]["exact"][-1000:]
                ordered = losses(target, ordered_ids)
                completed += 1
                advance(packet, "payoff", completed, total, "score calls")
                publish()
                yield
                unordered = losses(target, shuffled_ids)
                completed += 1
                advance(packet, "payoff", completed, total, "score calls")
                publish()
                yield
                code = source_holdouts(earlier, max(0, len(earlier["anchor"]["exact"]) - 1000))
                a, b = average(target, ordered, code=code), average(target, unordered, code=code)
                prior = " ".join(r["anchor"]["exact"] for r in regions[:regions.index(earlier)])
                blocked = copied_spans(target, prior + " " + text)
                na, nb = average(target, ordered, blocked, code), average(target, unordered, blocked, code)
                if a is not None and b is not None:
                    windows.append({"region": region["id"], "gain": b - a, "novelGain": nb - na if na is not None and nb is not None else None, "earlier": earlier["id"], "text": text})
            if windows:
                best = dict(max(windows, key=lambda r: r["gain"]))
                best["rate"] = best["gain"] / max(1, length)
                best["novelBestGain"] = max((r["novelGain"] for r in windows if r["novelGain"] is not None), default=None)
                best["novelRate"] = best["novelBestGain"] / max(1, length) if best["novelBestGain"] is not None else None
                late.append(best)
    top2 = sorted(late, key=lambda r: -r["rate"])[:3]
    novel2 = sorted([r for r in late if r["novelRate"] is not None], key=lambda r: -r["novelRate"])[:3]
    report["layer2NovelRetention"] = len({r["region"] for r in top2} & {r["region"] for r in novel2}) / len(top2) if top2 else None
    for index, row in enumerate(top2):
        span = {"region": row["region"], "start": 0, "end": utf16_length(row["text"])}
        score = relative(row["rate"], "Re-reading gain per token of the resolving passage, versus its sentence-shuffled control; nats/token, not measured enjoyment.", (min(-1, row["rate"]), max(1, row["rate"])))
        h = hypothesis(packet, ["reread", index], "Resolves fast" if row["gain"] > 0 else "No positive re-reading gain", f"Paragraph {row['region']}'s largest gain is {row['gain']:.3f} nats for earlier passage {row['earlier']} versus its sentence-shuffled control; novel-span gain {row['novelGain'] if row['novelGain'] is not None else 'unavailable'}. Gain per resolving token {row['rate']:.5f}. After this short passage, what came before reads more easily: a proxy for the aha, not measured enjoyment. A zero or negative gain does not show improvement. Every earlier paragraph's final 1,000 characters is compared at matched context-token positions. Four-token copies of the future paragraph are held out for the novel-span control. " + common,
                       kind="attention", regions=[row["region"]], support=score, spans=[span])
        packet.setdefault("currentAttention", []).append({"maker": h["makers"][0], "span": span, "items": [{"hypothesis": h["id"], "support": score, **LABELS}]})
    partition_attention(packet)
    report["layer2Status"] = "complete: earlier-paragraph windows with matched sentence-shuffle and novel-span controls"


def payoff(*args, **kwargs):
    for _ in payoff_steps(*args, **kwargs):
        pass
