"""Relational checks for engine-produced packets; zod parity remains mandatory."""

import re
from datetime import datetime

from ..adapters.capture import utf16_length


def validate_relations(packet):
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    def timestamp(value):
        require(
            bool(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z", value)),
            "Packet timestamp must be ISO UTC",
        )
        datetime.fromisoformat(value)

    def table(rows):
        require(all(0 < len(r.id) <= 200 for r in rows), "Invalid identifier length")
        require(len({r.id for r in rows}) == len(rows), "Duplicate packet IDs")
        return {r.id: r for r in rows}

    timestamp(packet.artifact.capturedAt)
    h = table(packet.hypotheses)
    makers = table(packet.makers)
    regions = table(packet.artifact.regions)
    for region in packet.artifact.regions:
        require(all(span.end <= utf16_length(region.anchor.exact) for span in region.codeSpans or []), "Code span outside captured region")
    evidence = table(packet.evidence)
    alternatives = table(packet.alternatives)
    hierarchy = table(packet.goalHierarchy.nodes if packet.goalHierarchy else [])
    if packet.preview and packet.preview.goalLenses is not None:
        lenses = packet.preview.goalLenses
        flattened = [ident for lens in lenses for ident in lens]
        require(len(lenses) == 2 and all(lenses), "Goal lenses require two nonempty views")
        require(len(flattened) == len(set(flattened)) and set(flattened) <= set(hierarchy), "Goal lenses must reference distinct available nodes")
        require(all(hierarchy[ident].parentId is None or hierarchy[ident].parentId in lens for lens in lenses for ident in lens), "Goal lens cannot separate a child from its parent")
    if packet.provider.mode == "preview":
        require(bool(packet.provider.previewNotice), "Preview requires its notice")
        require(packet.preview is not None, "Preview requires module status")
        labeled = [*packet.hypotheses, *hierarchy.values()]
        labeled.extend(item for frame in packet.currentAttention or [] for item in frame.items)
        require(all(row.evidenceStatus and row.basis for row in labeled), "Preview items require evidenceStatus and basis")
        scores = [row.support for row in packet.hypotheses]
        scores.extend(item.support for frame in packet.currentAttention or [] for item in frame.items)
        scores.extend(m.predictability for m in packet.makers)
        if packet.population:
            scores.extend(item.populationSupport for item in packet.population.items)
        require(all(score is None or score.semantics == "relative" for score in scores), "Preview support must be relative")
    else:
        require(packet.preview is None, "Preview output requires preview mode")
    for row in evidence.values():
        timestamp(row.capturedAt)
    for maker in makers.values():
        if maker.evidence is not None:
            require(packet.schemaVersion == "1.9", "Maker evidence requires contract 1.9")
            require(not any(e.tier == "statistical" for e in maker.evidence), "Statistical source signals are disabled")
            require(maker.kind == "unknown" or any(e.tier in {"signed", "declared", "flagged"} for e in maker.evidence), "Maker entries require signed, declared or flagged evidence")
    require(
        packet.scope.kind != "artifact" or not packet.scope.contextIds,
        "Artifact scope cannot use context",
    )

    def span(s):
        require(s.region in regions, "Unresolved span region")
        require(s.end <= utf16_length(regions[s.region].anchor.exact), "Span outside region")

    def refs(values, lookup):
        require(all(v in lookup for v in values), "Unresolved packet reference")

    def support(s, ident):
        if s is not None and s.candidateSet:
            require(
                s.candidateSet in alternatives and ident in alternatives[s.candidateSet].members,
                "Invalid support candidate set",
            )

    meanings = {
        "goal": {"local-goal", "governing-purpose"},
        "process": {"historical-event", "reader-route", "repertoire"},
        "value": {"value", "preference", "drive"},
        "attention": {"current-attention"},
    }
    for row in h.values():
        refs(row.makers, makers)
        refs(row.regions, regions)
        refs(row.evidence, evidence)
        require(
            row.interpretation is None or row.interpretation in meanings[row.kind],
            "Interpretation does not match hypothesis kind",
        )
        support(row.support, row.id)
        require(
            row.preferenceEstimate is None
            or (packet.schemaVersion in {"1.8", "1.9"} and row.kind == "value"),
            "Structured preference estimates require a value hypothesis in contract 1.8",
        )
        for s in row.spans or []:
            span(s)
            require(s.region in row.regions, "Hypothesis span outside associated regions")
        for node in row.decisionNodes or []:
            require(
                node in hierarchy and hierarchy[node].maker in row.makers,
                "Invalid hypothesis decision node",
            )
        if row.alternativeSet:
            require(
                row.alternativeSet in alternatives
                and row.id in alternatives[row.alternativeSet].members,
                "Invalid hypothesis alternative set",
            )

    def probabilities(scores, group):
        if (
            group.exhaustive
            and group.kind == "competing"
            and any(s and s.semantics == "probability" for s in scores)
        ):
            require(
                all(
                    s and s.semantics == "probability" and s.candidateSet == group.id
                    for s in scores
                ),
                "Incomplete exhaustive probability set",
            )
            require(
                abs(sum(s.value for s in scores) - 1) <= 1e-6,
                "Exhaustive probability set must sum to one",
            )

    for group in alternatives.values():
        refs(group.members, h)
        probabilities([h[i].support for i in group.members], group)
    for row in hierarchy.values():
        refs([row.maker], makers)
        refs(row.regions, regions)
        refs(row.evidence, evidence)
        if row.aiAttribution:
            refs(row.aiAttribution.evidence, evidence)
        require(not (row.parentIds and row.parentId), "Ambiguous hierarchy parents")
        parents = row.parentIds or ([row.parentId] if row.parentId else [])
        require(len(parents) == len(set(parents)), "Duplicate hierarchy parents")
        for parent in parents:
            require(
                parent in hierarchy and hierarchy[parent].maker == row.maker,
                "Invalid hierarchy parent",
            )
            require(
                set(row.regions) <= set(hierarchy[parent].regions), "Child outside parent regions"
            )
        if row.span:
            span(row.span)
            require(row.span.region in row.regions, "Hierarchy span outside regions")
        require(row.level != "sentence" or row.span is not None, "Sentence node needs a span")

    def acyclic(nodes, children, depth_limit=3000):
        done, active = {}, set()

        def visit(ident):
            require(ident not in active and len(active) < depth_limit, "Cyclic or too-deep graph")
            if ident in done:
                return done[ident]
            active.add(ident)
            depth = 1 + max([0] + [visit(other) for other in children(ident)])
            active.remove(ident)
            require(depth <= depth_limit, "Graph exceeds depth bound")
            done[ident] = depth
            return depth

        for ident in nodes:
            visit(ident)

    acyclic(
        hierarchy,
        lambda i: (
            hierarchy[i].parentIds or ([hierarchy[i].parentId] if hierarchy[i].parentId else [])
        ),
        64,
    )
    require(
        all(i in h and h[i].kind == "process" for i in packet.process.nodes),
        "Process node must be a process hypothesis",
    )
    for edge in packet.process.edges:
        refs([edge.from_, edge.to], packet.process.nodes)
        refs(edge.evidence or [], evidence)
    acyclic(
        packet.process.nodes,
        lambda i: [e.to for e in packet.process.edges if e.from_ == i and e.kind == "precedes"],
    )
    frames = sorted(
        packet.currentAttention or [], key=lambda f: (f.maker, f.span.region, f.span.start)
    )
    last = None
    for frame in frames:
        span(frame.span)
        refs([frame.maker], makers)
        require(
            len({i.hypothesis for i in frame.items}) == len(frame.items), "Duplicate attention item"
        )
        if last and last.maker == frame.maker and last.span.region == frame.span.region:
            require(last.span.end <= frame.span.start, "Overlapping attention frames")
        scores = {}
        for item in frame.items:
            require(item.hypothesis in h, "Unknown attention hypothesis")
            row = h[item.hypothesis]
            require(
                row.kind == "attention"
                and frame.maker in row.makers
                and (not row.regions or frame.span.region in row.regions),
                "Mismatched attention hypothesis",
            )
            scores[row.id] = item.support if "support" in item.model_fields_set else row.support
            support(scores[row.id], row.id)
        for group in alternatives.values():
            probabilities([scores.get(i) for i in group.members], group)
        last = frame
    refs([e.region for e in packet.estimates], regions)
    require(
        len({e.region for e in packet.estimates}) == len(packet.estimates), "Duplicate estimates"
    )
    for maker in makers.values():
        s = maker.predictability
        require(
            s is None or (s.semantics == "relative" and s.scale == (0, 1)),
            "Predictability requires a relative unit scale",
        )
    if packet.population:
        items = packet.population.items
        require(len({i.hypothesis for i in items}) == len(items), "Duplicate population item")
        for item in items:
            row = h.get(item.hypothesis)
            if item.quantiles is not None:
                require(all(item.populationSupport.scale[0] <= q <= item.populationSupport.scale[1] for q in item.quantiles), "Population quantile outside scale")
                require(all(a <= b for a, b in zip(item.quantiles, item.quantiles[1:])), "Population quantiles must be sorted")
            require(
                row and row.kind == "value" and len(row.makers) == 1,
                "Invalid population hypothesis",
            )
            support(item.populationSupport, item.hypothesis)
            require(
                row.support is None or row.support.scale == item.populationSupport.scale,
                "Population scale differs from maker scale",
            )
            require(
                item.makerRecords != 0 or item.shrinkage == 0, "No personal share without records"
            )
            require(
                all(a.records < b.records for a, b in zip(item.curve, item.curve[1:])),
                "Population curve records must increase",
            )
        for group in alternatives.values():
            scores = {i.hypothesis: i.populationSupport for i in items}
            probabilities([scores.get(i) for i in group.members], group)
