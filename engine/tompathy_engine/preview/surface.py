"""Word-aligned surface scoring and explicit names/numbers/code holdouts."""

import re
from statistics import mean

import numpy as np

from ..adapters.capture import utf16_length, utf16_slice

WORD = re.compile(r"\b\w+(?:['’]\w+)*\b", re.UNICODE)
CODE = re.compile(r"```[\s\S]*?```|`[^`]*`|https?://\S+|www\.\S+", re.IGNORECASE)
SENTENCE = re.compile(r"[^.!?\n]+(?:[.!?]+|$)")
STOP = frozenset(["a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "as", "is", "are", "was", "were", "be", "been", "it", "its", "this", "that", "at", "by", "from", "not", "i", "you", "he", "she", "they", "we"])


def source_holdouts(region, start=0, end=None):
    text = region["anchor"]["exact"]
    end = len(text) if end is None else end
    ranges = [(len(utf16_slice(text, 0, r["start"])), len(utf16_slice(text, 0, r["end"]))) for r in region.get("codeSpans", [])]
    return [(max(a, start) - start, min(b, end) - start) for a, b in ranges if a < end and b > start]


def words(text, tokens, held_spans=()):
    blocked = [*held_spans, *((m.start(), m.end()) for m in CODE.finditer(text))]
    out = []
    matches = list(WORD.finditer(text))
    byte_offsets = [0]
    for char in text:
        byte_offsets.append(byte_offsets[-1] + len(char.encode("utf8")))
    byte_at = byte_offsets.__getitem__
    cursor = 0
    for index, match in enumerate(matches):
        a, b = match.span()
        # Shared source spans include the following separators, rather than
        # assigning the leading space in a BPE token to its following word.
        span_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        while cursor < len(tokens) and tokens[cursor]["end"] <= a:
            cursor += 1
        scored = []
        j = cursor
        while j < len(tokens) and tokens[j]["start"] < span_end:
            token = tokens[j]
            overlap = byte_at(min(span_end, token["end"])) - byte_at(max(a, token["start"]))
            if overlap > 0:
                scored.append((token, overlap))
            j += 1
        if not scored:
            continue
        value = match.group()
        before = text[:a].rstrip(' \t\n\r“"‘([{')
        initial = not before or before[-1] in ".!?"
        held = any(c.isdigit() for c in value) or (value[0].isupper() and not initial) or any(a < y and b > x for x, y in blocked)
        # Byte-overlap allocation is an explicitly approximate attribution of
        # observed-token loss, not a normalized word probability. Exact boundary
        # marginalization needs next-token distributions, absent from this API.
        nats = sum(t["nats"] * overlap / (byte_at(t["end"]) - byte_at(t["start"])) for t, overlap in scored)
        out.append({"start": a, "end": b, "byteStart": byte_at(a), "byteEnd": byte_at(span_end), "text": value, "nats": nats, "held": held, "content": value.lower() not in STOP})
    return out


def score_regions(capture, reader, check=lambda: None, short=False, priority=None):
    """Visit priority first without changing any target's preceding context."""
    regions = capture["regions"]
    order = sorted(range(len(regions)), key=lambda i: regions[i]["id"] != priority)
    for index in order:
        region = regions[index]
        check()
        text = region["anchor"]["exact"]
        previous = regions[index - 1]["anchor"]["exact"] if index else ""
        if short:
            previous = ""
            for prior in reversed(regions[:index]):
                preceding = list(SENTENCE.finditer(prior["anchor"]["exact"]))
                if preceding:
                    previous = preceding[-1].group()
                    break
            tokens = []
            for sentence in SENTENCE.finditer(text):
                scored = reader.score(sentence.group(), previous, check)
                tokens.extend({**t, "start": t["start"] + sentence.start(), "end": t["end"] + sentence.start()} for t in scored)
                previous = sentence.group()
        else:
            chunks = reader.score_chunks(text, previous, check) if hasattr(reader, "score_chunks") else [(reader.score(text, previous, check), True)]
            for tokens, complete in chunks:
                # Never label unscored suffix words as if they had been read.
                end = len(text) if complete else tokens[-1]["end"] if tokens else 0
                # A tokenizer window can end inside a source word. Wait for the
                # remaining tokens before treating that word as a scored word.
                if not complete:
                    crossing = next((m for m in WORD.finditer(text) if m.start() < end < m.end()), None)
                    if crossing:
                        end = crossing.start()
                excerpt = text[:end]
                aligned = words(text, tokens, source_holdouts(region))
                byte_end = len(excerpt.encode("utf8"))
                aligned = [word for word in aligned if word["byteEnd"] <= byte_end]
                yield {"region": region["id"], "text": excerpt, "words": aligned, "complete": complete}
            continue
        yield {"region": region["id"], "text": text, "words": words(text, tokens, source_holdouts(region)), "complete": True}


def score_page(capture, reader, check=lambda: None, short=False):
    return [row for row in score_regions(capture, reader, check, short) if row["complete"]]


def deviation_map(capture, reader, check=lambda: None):
    rows = score_page(capture, reader, check)
    return summarize_deviation(rows, check)


def summarize_deviation(rows, check=lambda: None):
    content = [w["nats"] for row in rows for w in row["words"] if w["content"] and not w["held"]]
    held = [w["text"] for row in rows for w in row["words"] if w["held"]]
    if not content:
        raise ValueError("No scorable content words after names/numbers/code holdouts")
    median = float(np.median(content))
    iqr = float(np.quantile(content, .75) - np.quantile(content, .25))
    phrases, sentences = [], []
    def item(row, selected, text, start, end):
        value = mean(w["nats"] for w in selected)
        return {"region": row["region"], "start": utf16_length(row["text"][:start]), "end": utf16_length(row["text"][:end]),
                "text": text, "departure": (value - median) / iqr if iqr > 1e-12 else 0.0}
    for row in rows:
        check()
        for sentence in SENTENCE.finditer(row["text"]):
            selected = [w for w in row["words"] if sentence.start() <= w["start"] < sentence.end() and w["content"] and not w["held"]]
            if selected:
                sentences.append(item(row, selected, sentence.group().strip()[:250], sentence.start(), sentence.end()))
        for i, word in enumerate(row["words"]):
            if word["held"] or not word["content"]:
                continue
            group = row["words"][i:i + 3]
            # Never bridge a held-out name, code span or sentence boundary.
            if any(w["held"] for w in group) or re.search(r"[.!?\n]", row["text"][word["end"]:group[-1]["start"]]):
                group = [word]
            selected = [w for w in group if w["content"]]
            phrases.append(item(row, selected, row["text"][group[0]["start"]:group[-1]["end"]], group[0]["start"], group[-1]["end"]))
    top = []
    for phrase in sorted(phrases, key=lambda r: -r["departure"]):
        if not any(p["region"] == phrase["region"] and p["start"] < phrase["end"] and p["end"] > phrase["start"] for p in top):
            top.append(phrase)
        if len(top) == 15:
            break
    if sentences:
        threshold = float(np.quantile([s["departure"] for s in sentences], .9))
        top.extend(s for s in sentences if s["departure"] >= threshold)
    return {"attention": top[:500], "rows": rows,
            "statistics": {"mean": mean(content), "median": median, "iqr": iqr, "words": len(content), "heldOut": len(held), "heldOutExamples": list(dict.fromkeys(held))[:20]}}


def agreement_from_tables(capture, tables_by_condition):
    from scipy.stats import spearmanr

    def aligned(rows):
        return {(row["region"], w["byteStart"], w["byteEnd"]): w["nats"] for row in rows for w in row["words"] if w["content"] and not w["held"]}
    result, full_flags = {}, []
    for condition in ("short", "full"):
        tables = [aligned(rows) for rows in tables_by_condition[condition]]
        keys = sorted(set(tables[0]) & set(tables[1]))
        if not keys:
            raise ValueError("No common content-word spans for the two readers")
        values = [[table[key] for key in keys] for table in tables]
        rho = float(spearmanr(*values).statistic) if len(keys) > 1 and all(len(set(v)) > 1 for v in values) else None
        count = max(1, int(np.ceil(len(keys) * .1)))
        tops = [set(sorted(keys, key=lambda key: (-table[key], key))[:count]) for table in tables]
        result[condition] = {"spearman": rho, "overlap": len(tops[0] & tops[1]) / len(tops[0] | tops[1]), "words": len(keys)}
        if condition == "full":
            for region in capture["regions"]:
                flags = [i for i, top in enumerate(tops) if any(key[0] == region["id"] for key in top)]
                if flags:
                    full_flags.append({"region": region["id"], "readers": flags})
    return {**result, "regions": full_flags, "method": "Common UTF-8 word spans including trailing punctuation/space; crossing-token loss is allocated by byte overlap. Approximate token-loss attribution, not normalized word probabilities or the full boundary correction of Pimentel & Meister / Oh & Schuler (2024). Spearman and top-decile Jaccard exclude shared holdouts. Short context: previous sentence; full: preceding paragraph within 2,048 tokens. Agreement is not validation."}


def compare_readers(capture, readers, check=lambda: None):
    tables = {condition: [score_page(capture, r, check, short=condition == "short") for r in readers]
              for condition in ("short", "full")}
    return agreement_from_tables(capture, tables)
