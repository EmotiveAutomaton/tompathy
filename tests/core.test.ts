import { test } from "node:test";
import assert from "node:assert/strict";
import {
  createExample,
  exampleContext,
  exampleText,
} from "../src/core/example";
import {
  makeArtifact,
  matchPacket,
  parsePacket,
  SessionSchema,
} from "../src/core/model";
import {
  publicURL,
  retrieve,
  collectSources,
  contextSourceURL,
} from "../src/core/collector";
import { acceptRevision, analysisHandoff } from "../src/core/reading";
import { contextIdentity, mergeContext } from "../src/core/context";
import { createHash } from "node:crypto";
import {
  goalAt,
  goalTree,
  goalGraph,
  hierarchyLayout,
  reelCandidates,
} from "../src/core/hierarchy";
import { attentionAt } from "../src/core/attention";
import { sentences } from "../src/core/sentences";

test("goal hierarchy preserves exact sentence spans, branches and historical independence", async () => {
  const packet = await createExample(),
    nodes = packet.goalHierarchy!.nodes;
  const sentence = nodes.find((n) => n.id === "sentence-3-2")!;
  const text = packet.artifact.regions.find(
    (r) => r.id === sentence.span!.region,
  )!.anchor.exact;
  assert.equal(
    text.slice(sentence.span!.start, sentence.span!.end),
    "We counted pauses, sketched the paths people took, and listened when someone offered a comment.",
  );
  assert.equal(goalAt(nodes, "p4", sentence.span!.start)?.id, sentence.id);
  const graph = goalGraph(nodes);
  const paragraph = graph.byId.get("paragraph-3")!;
  assert.equal(graph.descendants(paragraph).size, 5);
  assert.deepEqual(
    [...graph.ancestors(paragraph)].sort(),
    ["paragraph-3", "story", "purpose", "practical-care"].sort(),
  );
  const legacy = legacyExample(packet);
  legacy.schemaVersion = "1.0";
  delete legacy.goalHierarchy;
  legacy.hypotheses.forEach((h) => {
    delete h.decisionNodes;
    delete h.spans;
  });
  assert.equal(parsePacket(JSON.stringify(legacy)).goalHierarchy, undefined);
  assert.ok(legacy.process.edges.length);
});

test("invalid hierarchy cycles, ranges, decision sources and wrong parents are rejected", async () => {
  const original = await createExample();
  for (const corrupt of [
    (p: typeof original) => {
      p.goalHierarchy!.nodes[0].parentId = "sentence-3-2";
    },
    (p: typeof original) => {
      p.goalHierarchy!.nodes.find((n) => n.span)!.span!.end = 90000;
    },
    (p: typeof original) => {
      p.goalHierarchy!.nodes.find((n) => n.id === "paragraph-3")!.parentId =
        "limits";
    },
    (p: typeof original) => {
      p.hypotheses[0].decisionNodes = ["missing"];
    },
  ]) {
    const packet = structuredClone(original);
    corrupt(packet);
    assert.throws(() => parsePacket(JSON.stringify(packet)));
  }
  const text = "Café 世界. A second sentence! A final question?";
  const spans = sentences(text);
  assert.equal(spans.length, 3);
  spans.forEach((s) => assert.equal(text.slice(s.start, s.end), s.text));
});

test(
  "the collection deadline cancels an unresponsive source without returning late context",
  { timeout: 35000 },
  async () => {
    const originalFetch = globalThis.fetch;
    let attempts = 0,
      results = 0;
    const keepAlive = setTimeout(() => {}, 34000);
    globalThis.fetch = async (_url, options) => {
      attempts++;
      return new Promise((_resolve, reject) => {
        options!.signal!.addEventListener(
          "abort",
          () => reject(new DOMException("Aborted", "AbortError")),
          { once: true },
        );
      });
    };
    try {
      await assert.rejects(
        collectSources(
          ["https://example.com/slow"],
          new AbortController().signal,
          () => results++,
        ),
        /timed out after 30 seconds/,
      );
      assert.equal(attempts, 1);
      assert.equal(results, 0);
    } finally {
      clearTimeout(keepAlive);
      globalThis.fetch = originalFetch;
    }
  },
);

test("example has anchored independent goals, stable values, and an explicit correction", async () => {
  const p = await createExample(),
    r = await createExample("tompathy:example", true);
  assert.equal(matchPacket(p, p.artifact, "artifact", []), null);
  assert.equal(
    matchPacket(
      p,
      await makeArtifact(exampleText, "tompathy:example", "Example"),
      "artifact",
      [],
    ),
    null,
  );
  assert.equal(matchPacket(r, p.artifact, "context", [exampleContext]), null);
  assert.notEqual(
    r.hypotheses.find((h) => h.id === "craft")?.label,
    p.hypotheses.find((h) => h.id === "craft")?.label,
  );
  assert.equal(r.revisionOf, p.id);
  assert.equal(
    p.hypotheses
      .filter((h) => h.kind === "value")
      .every((h) => !h.regions.length),
    true,
  );
});
test("repeated Unicode and inline-compatible text get distinct contextual anchors", async () => {
  const a = await makeArtifact(
    ["Hello café — 世界", "Repeated phrase here.", "Repeated phrase here."],
    "https://example.com",
    "Test",
  );
  assert.notEqual(a.regions[1].anchor.start, a.regions[2].anchor.start);
  assert.notEqual(a.regions[1].anchor.prefix, a.regions[2].anchor.prefix);
  const p = await createExample();
  assert.match(matchPacket(p, a, "artifact", [])!, /different artifact/);
  const corrupt = structuredClone(p);
  corrupt.artifact.regions[0].anchor.index = 9;
  assert.match(matchPacket(corrupt, p.artifact, "artifact", [])!, /anchors/);
});
test("missing support and zero remain distinct; invalid numbers and dangling references fail", async () => {
  const p = await createExample();
  const h = p.hypotheses.find((h) => h.id === "invite")!;
  h.support!.value = 0;
  assert.equal(
    parsePacket(JSON.stringify(p)).hypotheses.find((h) => h.id === "invite")!
      .support?.value,
    0,
  );
  h.support!.value = 2;
  assert.throws(() => parsePacket(JSON.stringify(p)), /outside declared scale/);
  h.support = null;
  h.evidence = ["missing"];
  assert.throws(() => parsePacket(JSON.stringify(p)), /Unresolved/);
  assert.throws(() => parsePacket("{broken"), SyntaxError);
});
test("probabilities require a valid candidate set, scale and normalized exhaustive distribution", async () => {
  const p = await createExample();
  const ids = ["observe", "convention"];
  for (const id of ids) {
    const h = p.hypotheses.find((h) => h.id === id)!;
    h.support = {
      value: 0.8,
      scale: [0, 1],
      semantics: "probability",
      meaning: "Test probability",
      candidateSet: "routes",
    };
  }
  p.alternatives.find((a) => a.id === "routes")!.exhaustive = true;
  assert.throws(() => parsePacket(JSON.stringify(p)), /sum to 1/);
  p.hypotheses.find((h) => h.id === "convention")!.support!.value = 0.2;
  assert.doesNotThrow(() => parsePacket(JSON.stringify(p)));
});
test("scope mismatches never re-use analysis and session validation catches corrupted packets", async () => {
  const p = await createExample();
  assert.match(
    matchPacket(p, p.artifact, "context", [exampleContext])!,
    /scope differs/,
  );
  const s = {
    sessionVersion: "1.0",
    artifact: p.artifact,
    packet: p,
    scope: "artifact",
    context: [],
  };
  assert.equal(SessionSchema.safeParse(s).success, true);
  p.process.edges[0].to = "absent";
  assert.equal(SessionSchema.safeParse(s).success, false);
});
test("public collector rejects private literals, encoded IPs, credentials, insecure and local sources", () => {
  for (const url of [
    "http://example.com",
    "https://localhost",
    "https://127.0.0.1",
    "https://2130706433",
    "https://[::1]",
    "https://192.168.1.1",
    "https://router.local",
    "https://host.internal",
    "https://user:pass@example.com",
    "https://example.com:9443",
  ])
    assert.throws(() => publicURL(url), url);
  assert.equal(
    publicURL("https://example.com/a#b").href,
    "https://example.com/a",
  );
});
test("bounded fetch rejects status, content type and oversized body; cancellation stays visible", async () => {
  const call = (response: Response) =>
    retrieve(
      new URL("https://example.com"),
      new AbortController().signal,
      async () => response,
    );
  await assert.rejects(call(new Response("no", { status: 404 })), /404/);
  await assert.rejects(
    call(new Response("x", { headers: { "content-type": "application/pdf" } })),
    /Choose an HTML/,
  );
  await assert.rejects(
    call(
      new Response("x".repeat(256001), {
        headers: { "content-type": "text/plain" },
      }),
    ),
    /256 KB/,
  );
  const r = await call(
    new Response("A useful public excerpt.", {
      headers: { "content-type": "text/plain" },
    }),
  );
  assert.equal(r.selected, false);
  assert.equal(r.lineage, "public-url");
});

test("historical partial orders, joint accounts and typed meanings reject contradictory references", async () => {
  const p = await createExample();
  assert.equal(p.schemaVersion, "1.4");
  assert.equal(p.alternatives[0].kind, "coexisting");
  p.process.edges.push({
    from: "iterate",
    to: "observe",
    kind: "precedes",
    relationship: "Invalid reverse chronology",
  });
  assert.throws(() => parsePacket(JSON.stringify(p)), /precedence.*cycle/);
  p.process.edges.pop();
  p.accounts![0].members.push("missing");
  assert.throws(() => parsePacket(JSON.stringify(p)), /Invalid members/);
  p.accounts![0].members.pop();
  p.documentContribution!.evidence.push("missing");
  assert.throws(
    () => parsePacket(JSON.stringify(p)),
    /Unresolved contribution/,
  );
  p.documentContribution!.evidence.pop();
  p.hypotheses[0].interpretation = "preference";
  assert.throws(
    () => parsePacket(JSON.stringify(p)),
    /Interpretation does not match/,
  );
});

test("legacy Stage 13 shape remains readable and missing values stay unknown", async () => {
  const p = legacyExample(await createExample());
  p.schemaVersion = "1.0";
  delete p.accounts;
  delete p.documentContribution;
  delete p.process.interpretation;
  p.process.edges = [];
  p.alternatives[0].kind = "independent";
  p.hypotheses.forEach((h) => delete h.interpretation);
  p.hypotheses
    .filter((h) => h.kind === "value")
    .forEach((h) => {
      h.status = "unknown";
      h.support = null;
    });
  p.estimates.forEach((e) => {
    e.contribution = null;
  });
  const parsed = parsePacket(JSON.stringify(p));
  assert.equal(
    parsed.estimates.every((e) => e.contribution === null),
    true,
  );
  assert.equal(
    parsed.hypotheses.filter(
      (h) => h.kind === "value" && h.status !== "unknown",
    ).length,
    0,
  );
});

test("accepted revision retains inspectable history; requests contain only selected evidence", async () => {
  const first = await createExample(),
    next = await createExample(undefined, true);
  const session = SessionSchema.parse({
    sessionVersion: "1.0",
    artifact: first.artifact,
    packet: first,
    scope: "artifact",
    context: [],
  });
  const accepted = acceptRevision(session, next, [exampleContext]);
  assert.equal(accepted.history![0].packet.id, first.id);
  assert.equal(accepted.packet!.id, next.id);
  const request = analysisHandoff({
    ...accepted,
    context: [
      exampleContext,
      { ...exampleContext, id: "unselected", selected: false },
    ],
  });
  assert.deepEqual(request.scope.contextIds, [exampleContext.id]);
  assert.equal(request.context.length, 1);
  assert.equal(
    analysisHandoff({ ...accepted, scope: "artifact" }).context.length,
    0,
  );
  assert.equal(session.history, undefined);
});

test("context identity binds Unicode source and excerpt; duplicate history is not counted twice", async () => {
  const source = "https://example.com/notes",
    excerpt = "A café — 世界";
  const id = await contextIdentity(source, excerpt);
  assert.equal(
    id,
    createHash("sha256")
      .update(JSON.stringify([source, excerpt]))
      .digest("hex"),
  );
  assert.notEqual(id, await contextIdentity(source, excerpt + " changed"));
  const item = { ...exampleContext, id, source, excerpt };
  assert.equal(mergeContext([item], { ...item, id: "legacy-id" }).length, 1);
});

test("1.3 accepts unnamed deep goal paths while retaining cycle, depth and legacy checks", async () => {
  const p = legacyExample(await createExample());
  p.schemaVersion = "1.3";
  const base = p.goalHierarchy!.nodes[0];
  p.hypotheses.forEach((h) => delete h.decisionNodes);
  const chain = (count: number) =>
    Array.from({ length: count }, (_, i) => ({
      ...base,
      id: `deep-${i}`,
      parentId: i ? `deep-${i - 1}` : undefined,
      level: undefined,
    }));
  p.goalHierarchy!.nodes = chain(64);
  assert.equal(
    goalTree(parsePacket(JSON.stringify(p)).goalHierarchy!.nodes)!.height,
    63,
  );
  assert.equal(goalAt(p.goalHierarchy!.nodes, "p4", 0)?.id, "deep-63");
  p.goalHierarchy!.nodes = chain(65);
  assert.throws(() => parsePacket(JSON.stringify(p)), /at most 64 levels/);
  p.goalHierarchy!.nodes = chain(7);
  p.goalHierarchy!.nodes[0].parentId = "deep-6";
  assert.throws(() => parsePacket(JSON.stringify(p)), /acyclic/);
  delete p.goalHierarchy!.nodes[0].parentId;
  p.schemaVersion = "1.2";
  assert.throws(
    () => parsePacket(JSON.stringify(p)),
    /requires a supported level/,
  );
});

// Deliberately convert only the new contract fields for legacy acceptance checks.
function legacyExample(packet: Awaited<ReturnType<typeof createExample>>) {
  const p = structuredClone(packet);
  delete p.currentAttention;
  p.hypotheses = p.hypotheses.filter((h) => h.kind !== "attention");
  p.goalHierarchy!.nodes = p.goalHierarchy!.nodes.filter(
    (n) => n.id !== "practical-care",
  );
  for (const n of p.goalHierarchy!.nodes)
    if (n.parentIds) {
      n.parentId = n.parentIds[0];
      delete n.parentIds;
    }
  return p;
}

test("independent attention supports sub-sentence snapshots and rejects invalid bindings", async () => {
  const p = await createExample();
  const frame = p.currentAttention!.find((f) => f.span.region === "p4")!;
  const first = attentionAt(p, "maker-1", "p4", frame.span.start);
  assert.equal(first[0].label, "Watching closely");
  assert.ok(first.every((h) => h.kind === "attention"));
  assert.ok(
    first.every((h) => !p.goalHierarchy!.nodes.some((n) => n.id === h.id)),
  );
  assert.equal(attentionAt(p, "unknown", "p4", 0).length, 0);
  const next = structuredClone(frame);
  next.span.start = 20;
  frame.span.end = 20;
  next.items.reverse();
  p.currentAttention!.push(next);
  assert.doesNotThrow(() => parsePacket(JSON.stringify(p)));
  assert.notEqual(
    attentionAt(p, "maker-1", "p4", 19)[0].id,
    attentionAt(p, "maker-1", "p4", 20)[0].id,
  );
  for (const change of [
    (q: typeof p) => {
      q.currentAttention![0].items[0].hypothesis = "invite";
    },
    (q: typeof p) => {
      q.currentAttention![0].span.end = 90000;
    },
    (q: typeof p) => {
      q.currentAttention!.push(q.currentAttention![0]);
    },
    (q: typeof p) => {
      q.currentAttention![0].items[0].support!.value = 2;
    },
    (q: typeof p) => {
      q.schemaVersion = "1.3";
    },
  ]) {
    const q = structuredClone(p);
    change(q);
    assert.throws(() => parsePacket(JSON.stringify(q)));
  }
  // Omitted support inherits the supplied baseline; explicit null stays unknown.
  const item = frame.items[0],
    hypothesis = p.hypotheses.find((h) => h.id === item.hypothesis)!;
  hypothesis.support = item.support;
  delete item.support;
  assert.equal(attentionAt(p, "maker-1", "p4", 0)[0].support!.value, 0.94);
  item.support = null;
  assert.equal(attentionAt(p, "maker-1", "p4", 0)[0].support, null);
});

test("two peaks retain shared parents, ambiguity in both directions, and usable brick edges", async () => {
  const p = await createExample(),
    graph = goalGraph(p.goalHierarchy!.nodes);
  assert.deepEqual(
    graph.roots.map((n) => [n.id, n.rank]),
    [
      ["purpose", 3],
      ["practical-care", 2],
    ],
  );
  const paragraph = graph.byId.get("paragraph-3")!;
  assert.equal(reelCandidates(graph, paragraph, 0).nodes.length, 4);
  assert.deepEqual(
    reelCandidates(graph, paragraph, 2)
      .nodes.map((n) => n.id)
      .sort(),
    ["practical-care", "story"],
  );
  assert.equal(reelCandidates(graph, paragraph, 3).ended, true);
  assert.equal(reelCandidates(graph, paragraph, 3).ambiguous, true);
  for (const nodes of [
    p.goalHierarchy!.nodes,
    legacyExample(p).goalHierarchy!.nodes,
  ]) {
    for (const height of [160, 300, 550]) {
      const g = goalGraph(nodes),
        layout = hierarchyLayout(g, height);
      assert.ok(layout.tiles.length >= nodes.length);
      const byKey = new Map(layout.tiles.map((t) => [t.key, t]));
      for (const tile of layout.tiles) {
        if (tile.parentKey) {
          const parent = byKey.get(tile.parentKey)!;
          assert.ok(parent.node.children.some((c) => c.id === tile.node.id));
          assert.ok(
            tile.from >= parent.from - 1e-9 && tile.to <= parent.to + 1e-9,
          );
          assert.equal(tile.x + tile.width, parent.x);
          assert.equal(tile.rootId, parent.rootId);
        }
      }
      assert.equal(
        new Set(layout.tiles.map((t) => t.node.id)).size,
        nodes.length,
      );
      for (const tile of layout.tiles) {
        assert.ok(tile.exposure >= 0.5, tile.node.id);
        assert.ok(tile.dotX > tile.x && tile.dotX < tile.x + tile.width);
        assert.ok(tile.dotY > tile.y && tile.dotY < tile.y + tile.height);
        assert.ok(
          layout
            .slices(tile.dotX)
            .some(([a, b]) => tile.dotY >= a && tile.dotY <= b),
        );
      }
    }
  }
  const cyclic = structuredClone(p);
  cyclic.goalHierarchy!.nodes.find(
    (n) => n.id === "practical-care",
  )!.parentIds = ["paragraph-3"];
  assert.throws(() => parsePacket(JSON.stringify(cyclic)), /acyclic/);
  const wrongParent = structuredClone(p);
  wrongParent.goalHierarchy!.nodes.find(
    (n) => n.id === "paragraph-3",
  )!.parentIds = ["story", "limits"];
  assert.throws(() => parsePacket(JSON.stringify(wrongParent)), /parent/);
});

test("GitHub context uses only explicit profiles and preserves the meaning of dates", async () => {
  assert.equal(
    contextSourceURL("https://github.com/octocat", true).href,
    "https://api.github.com/users/octocat",
  );
  assert.equal(
    contextSourceURL("https://github.com/octocat", false).href,
    "https://github.com/octocat",
  );
  assert.equal(
    contextSourceURL("https://github.com/owner/project", true).href,
    "https://github.com/owner/project",
  );
  assert.equal(
    contextSourceURL("https://github.com/features", true).href,
    "https://github.com/features",
  );
  const input = new URL("https://api.github.com/users/octocat");
  const response = () =>
    new Response(
      JSON.stringify({
        login: "octocat",
        bio: "Writes about design",
        created_at: "2011-01-25T18:44:36Z",
        updated_at: "2026-10-11T12:00:00Z",
      }),
      { headers: { "content-type": "application/json" } },
    );
  const item = await retrieve(
    input,
    new AbortController().signal,
    async (_url, opts) => {
      assert.equal(opts?.credentials, "omit");
      return response();
    },
  );
  assert.match(item.excerpt, /Account created: 2011/);
  assert.match(item.excerpt, /Profile updated: 2026/);
  assert.equal(item.selected, false);
  await assert.rejects(
    retrieve(
      new URL("https://api.github.com/users/another"),
      new AbortController().signal,
      async () => response(),
    ),
    /does not match/,
  );
});
