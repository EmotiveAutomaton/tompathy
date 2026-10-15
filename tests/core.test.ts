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
  instanceNeighborhood,
  instanceReelCandidates,
} from "../src/core/hierarchy";
import { calendarDate } from "../src/core/dates";
import { blockedFocusTracker } from "../src/core/lock";
import { readingFile, parseReadingFile } from "../src/core/reading-file";
import {
  retrieveGitHubContext,
  githubRepository,
} from "../src/core/github-context";
import { ContextSchema } from "../src/core/model";

test("explicit GitHub file history resolves slash refs, preserves provenance and respects bounds", async () => {
  const calls: string[] = [];
  const sha = "a".repeat(40);
  const fetcher = (async (input: string, options: RequestInit) => {
    calls.push(input);
    assert.equal(options.credentials, "omit");
    assert.equal(options.redirect, "error");
    const url = new URL(input);
    let data: unknown;
    if (url.pathname.endsWith("/docs"))
      data = {
        private: false,
        default_branch: "main",
        description: "A public essay",
      };
    else if (url.pathname.includes("/contents/revision/"))
      return new Response("", { status: 404 });
    else if (url.pathname.endsWith("/contents/article.md")) {
      assert.equal(url.searchParams.get("ref"), "draft/revision");
      data = {
        type: "file",
        path: "article.md",
        encoding: "base64",
        content: btoa("An explicit source file."),
      };
    } else if (url.pathname.endsWith("/commits")) {
      assert.equal(url.searchParams.get("path"), "article.md");
      data = [
        {
          sha,
          commit: {
            author: { name: "A contributor", date: "2024-03-01T12:00:00Z" },
            committer: { date: "2024-03-02T12:00:00Z" },
            message: "Clarify wording",
          },
        },
      ];
    } else
      data = {
        files: [
          {
            filename: "article.md",
            status: "modified",
            additions: 2,
            deletions: 1,
            patch: "-before\n+after",
          },
        ],
      };
    return Response.json(data);
  }) as typeof fetch;
  const result = await retrieveGitHubContext(
    new URL("https://github.com/example/docs/blob/draft/revision/article.md"),
    new AbortController().signal,
    fetcher,
  );
  assert.equal(calls.length, 5);
  assert.equal(result.item.facts?.[2].date, "2024-03-01");
  assert.match(result.item.excerpt, /committer timestamp: 2024-03-02/);
  assert.match(result.item.excerpt, /\+after/);
  assert.match(result.item.excerpt, /do not establish who wrote/);
  assert.equal(ContextSchema.safeParse(result.item).success, true);
  assert.equal(
    githubRepository("https://github.com/example/docs/issues/1"),
    null,
  );
  let attempts = 0;
  await assert.rejects(
    () =>
      retrieveGitHubContext(
        new URL("https://github.com/example/docs"),
        new AbortController().signal,
        (async () => {
          attempts++;
          return new Response("limited", { status: 403 });
        }) as typeof fetch,
      ),
    /rate limit/,
  );
  assert.equal(attempts, 1);
  await assert.rejects(
    () =>
      retrieveGitHubContext(
        new URL("https://github.com/example/docs"),
        new AbortController().signal,
        (async () =>
          new Response("{}", {
            headers: {
              "content-type": "application/json",
              "content-length": "256001",
            },
          })) as typeof fetch,
      ),
    /256 KB/,
  );
});

test("lock reminder rejects jitter and slow exploration, bounds bursts, and resets", () => {
  const tracker = blockedFocusTracker();
  for (let i = 0; i < 50; i++)
    assert.equal(tracker.attempt("same", i * 50), false);
  tracker.reset();
  for (let i = 0; i < 5; i++)
    assert.equal(tracker.attempt(String(i), i * 1500), false);
  tracker.reset();
  for (let i = 0; i < 11; i++)
    assert.equal(tracker.attempt(String(i), i * 75), false);
  assert.equal(tracker.attempt("last", 825), true);
  for (let i = 0; i < 50; i++)
    assert.equal(tracker.attempt(String(i), 900 + i * 100), false);
  tracker.acknowledge(6000);
  assert.equal(tracker.attempt("remote", 6100, 2), false);
  tracker.reset();
  for (let i = 0; i < 5; i++)
    assert.equal(tracker.attempt(String(i), i * 100, 2), false);
  assert.equal(tracker.attempt("sixth sentence", 500, 2), true);
  tracker.reset();
  for (let i = 0; i < 8; i++)
    assert.equal(tracker.attempt(String(i), i * 75, i < 3 ? 2 : 1), false);
  assert.equal(tracker.attempt("mixed final", 600), true);
});

test("reading export round-trips pending context without losing the previous account", async () => {
  const packet = await createExample();
  const session = {
    sessionVersion: "1.0" as const,
    artifact: packet.artifact,
    packet,
    context: [{ ...exampleContext, selected: true }],
    scope: "context" as const,
  };
  const restored = await parseReadingFile(readingFile(session));
  assert.equal(restored.packet, null);
  assert.equal(restored.scope, "context");
  assert.equal(restored.context[0].selected, true);
  assert.deepEqual(restored.history![0].packet, packet);
  const tampered = structuredClone(session);
  tampered.artifact.regions[0].anchor.exact =
    "A changed source must still be rejected.";
  // Separate the packet and artifact: structuredClone preserves shared references.
  tampered.packet = structuredClone(packet);
  assert.throws(() => readingFile(tampered), /anchors do not match/);
  const legacy = { ...session, scope: "artifact" as const, context: [] };
  assert.deepEqual(
    (await parseReadingFile(readingFile(legacy))).packet,
    packet,
  );
});
import {
  clearContextCache,
  collectCreatorContext,
  contextTimeline,
  contextBrief,
} from "../src/core/creator-context";
import { attentionAt, attentionForNode } from "../src/core/attention";

test("branch attention retains every distinct supplied focus without duplicating shared sentences", async () => {
  const packet = await createExample();
  const nodes = packet.goalHierarchy!.nodes;
  const leaf = nodes.find((n) => n.id === "sentence-3-2")!;
  assert.deepEqual(
    attentionForNode(packet, "maker-1", leaf),
    attentionAt(packet, "maker-1", "p4", leaf.span!.start),
  );
  const paragraph = nodes.find((n) => n.id === "paragraph-3")!;
  const frames = packet.currentAttention!.filter((f) => f.span.region === "p4");
  const overview = attentionForNode(packet, "maker-1", paragraph);
  assert.deepEqual(
    new Set(overview.map((h) => h.id)),
    new Set(frames.flatMap((f) => f.items.map((i) => i.hypothesis))),
  );
  assert.ok(overview.length > 6);
  const focus = overview.find((h) => h.id === "focus-11")!;
  const expected =
    frames.reduce(
      (sum, f) =>
        sum +
        (f.items.find((i) => i.hypothesis === focus.id)?.support?.value ?? 0),
      0,
    ) / 4;
  assert.equal(focus.support!.value, expected);
  assert.equal(focus.support!.semantics, "relative");
  assert.deepEqual(
    attentionForNode(
      packet,
      "maker-1",
      nodes.find((n) => n.id === "assembly")!,
    ),
    [],
  );
  assert.deepEqual(attentionForNode(packet, "unknown", paragraph), []);
  // A duplicate path in the graph is not a duplicate observation.
  const extra = structuredClone(paragraph);
  extra.id = "parallel-process";
  extra.parentId = "story";
  nodes.push(extra);
  const shared = nodes.find((n) => n.id === "sentence-3-1")!;
  shared.parentIds = ["paragraph-3", "parallel-process"];
  const before = attentionForNode(
    packet,
    "maker-1",
    nodes.find((n) => n.id === "story")!,
  );
  shared.parentIds = ["paragraph-3"];
  assert.deepEqual(
    attentionForNode(
      packet,
      "maker-1",
      nodes.find((n) => n.id === "story")!,
    ),
    before,
  );
});
import { sentences } from "../src/core/sentences";
import { ghostAt, ghostInk, contrast, rgb, grade } from "../src/core/ghost";

test("Ghost Scale is independent, creator-bound, contrast-safe and portable", async () => {
  const p = await createExample(),
    first = p.ghostReadings![0];
  assert.equal(
    ghostAt(
      p,
      "someone-else",
      first.span.region,
      first.span.start,
      first.span.end,
    ),
    undefined,
  );
  assert.equal(grade(null), 0);
  assert.equal(grade(0), -50);
  assert.equal(grade(1), 100);
  for (const [foreground, background] of [
    [
      [38, 58, 50],
      [250, 249, 245],
    ],
    [
      [224, 232, 225],
      [31, 43, 38],
    ],
    [
      [140, 140, 140],
      [255, 255, 255],
    ],
  ] as [number[], number[]][]) {
    for (const kind of ["original", "edited", "curated", "ghost"] as const) {
      const ink = ghostInk(
        kind,
        foreground as [number, number, number],
        background as [number, number, number],
      );
      assert.ok(
        contrast(
          rgb(ink.color),
          kind === "ghost"
            ? rgb(ink.background)
            : (background as [number, number, number]),
        ) >= 4.5,
      );
    }
  }
  assert.equal(ghostInk("edited", [38, 58, 50], [250, 249, 245]).opacity, 0.95);
  for (const change of [
    (q: typeof p) => (q.ghostReadings![0].maker = "missing"),
    (q: typeof p) => (q.ghostReadings![0].evidence = ["missing"]),
    (q: typeof p) => (q.ghostReadings![0].span.end = 99999),
    (q: typeof p) =>
      q.ghostReadings!.push(structuredClone(q.ghostReadings![0])),
    (q: typeof p) => (q.ghostReadings![0].confidence = 1.1),
    (q: typeof p) => (q.ghostReadings![0].span.start = 1),
  ]) {
    const q = structuredClone(p);
    change(q);
    assert.throws(() => parsePacket(JSON.stringify(q)));
  }
  const session = {
    sessionVersion: "1.0" as const,
    artifact: p.artifact,
    packet: p,
    context: [{ ...exampleContext, selected: false }],
    scope: "artifact" as const,
  };
  const exported = readingFile(session),
    imported = await parseReadingFile(exported);
  assert.match(exported, /<strong>leaving enough time<\/strong>/);
  assert.deepEqual(imported.packet!.ghostReadings, p.ghostReadings);
  assert.deepEqual(
    imported.artifact!.regions[2].emphasis,
    p.artifact.regions[2].emphasis,
  );
  assert.equal(imported.context[0].facts!.length, 5);
});

test("goal hierarchy preserves exact sentence spans, branches and historical independence", async () => {
  const packet = await createExample(),
    nodes = packet.goalHierarchy!.nodes;
  const sentence = nodes.find((n) => n.id === "sentence-3-2")!;
  const text = packet.artifact.regions.find(
    (r) => r.id === sentence.span!.region,
  )!.anchor.exact;
  assert.equal(
    text.slice(sentence.span!.start, sentence.span!.end),
    "A tester pointed out that I kept calling silence confusion when it sometimes meant someone was waiting for their partner.",
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
  assert.equal(p.schemaVersion, "1.6");
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
  delete p.ghostReadings;
  delete p.currentAttention;
  delete p.goalHierarchy?.orderUncertainGroups;
  p.hypotheses = p.hypotheses.filter((h) => h.kind !== "attention");
  p.goalHierarchy!.nodes = p.goalHierarchy!.nodes.filter(
    (n) => n.id !== "practical-care",
  );
  for (const n of p.goalHierarchy!.nodes)
    if (n.parentIds) {
      n.parentId = n.parentIds[0];
      delete n.parentIds;
    }
  for (const n of p.goalHierarchy!.nodes)
    if (n.id !== "purpose" && !n.parentId) n.parentId = "purpose";
  return p;
}

test("independent attention supports sub-sentence snapshots and rejects invalid bindings", async () => {
  const p = await createExample();
  const frame = p.currentAttention!.find((f) => f.span.region === "p4")!;
  const first = attentionAt(p, "maker-1", "p4", frame.span.start);
  assert.equal(first[0].label, "Watching the players");
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

test("story branches retain shared parents, ambiguity in both directions, and usable brick edges", async () => {
  const p = await createExample(),
    graph = goalGraph(p.goalHierarchy!.nodes);
  assert.deepEqual(
    graph.roots.map((n) => [n.id, n.rank]),
    [
      ["purpose", 4],
      ["next-test", 2],
      ["practical-care", 2],
      ["assembly", 1],
    ],
  );
  const paragraph = graph.byId.get("paragraph-3")!;
  for (const reading of p.ghostReadings ?? []) {
    const leaf = goalAt(
      p.goalHierarchy!.nodes,
      reading.span.region,
      reading.span.start,
    );
    assert.deepEqual(
      leaf?.span,
      reading.span,
      "Every sentence must remain reachable, including later paragraphs",
    );
  }
  assert.equal(reelCandidates(graph, paragraph, 0).nodes.length, 4);
  assert.deepEqual(
    reelCandidates(graph, paragraph, 2)
      .nodes.map((n) => n.id)
      .sort(),
    ["practical-care", "story"],
  );
  assert.equal(reelCandidates(graph, paragraph, 4).ended, true);
  assert.equal(reelCandidates(graph, paragraph, 4).ambiguous, true);
  for (const nodes of [
    p.goalHierarchy!.nodes,
    legacyExample(p).goalHierarchy!.nodes,
  ]) {
    for (const height of [160, 300, 550]) {
      const g = goalGraph(nodes),
        layout = hierarchyLayout(g, height);
      assert.equal(layout.tiles.length, nodes.length);
      const widths = layout.edges
        .slice(1)
        .map((edge, i) => edge - layout.edges[i]);
      assert.equal(widths.indexOf(Math.max(...widths)), layout.usefulTier);
      assert.ok(widths.every((w) => w > 0));
      assert.ok(
        Math.abs(widths.reduce((a, b) => a + b, 0) - layout.width) < 1e-7,
      );

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

test("one visual home per sentence, semantic extra parents, and one smooth leaf arc", async () => {
  const packet = await createExample(),
    graph = goalGraph(packet.goalHierarchy!.nodes);
  for (const height of [160, 300, 550]) {
    const layout = hierarchyLayout(graph, height);
    assert.equal(layout.tiles.length, graph.all.length);
    const leaves = layout.tiles.filter((t) => t.node.data.span);
    assert.equal(leaves.length, 30);
    assert.equal(new Set(leaves.map((t) => t.node.id)).size, 30);
    assert.equal(layout.links.length, 3);
    for (const link of layout.links) {
      const corners = (id: string) => {
        const tile = layout.tiles.find((t) => t.node.id === id)!;
        const points = [...tile.path.matchAll(/(-?[\d.]+),(-?[\d.]+)/g)].map(
          (p) => ({ x: Number(p[1]), y: Number(p[2]) }),
        );
        return [
          Math.min(...points.map((p) => p.x)),
          Math.max(...points.map((p) => p.x)),
        ].flatMap((x) => points.filter((p) => p.x === x));
      };
      const [x1, y1, y2, x2] = link.path.match(/-?[\d.]+/g)!.map(Number);
      const distance = Math.abs(x2 - x1) + Math.abs(y2 - y1);
      const shortest = Math.min(
        ...corners(link.child).flatMap((a) =>
          corners(link.parent).map(
            (b) => Math.abs(a.x - b.x) + Math.abs(a.y - b.y),
          ),
        ),
      );
      assert.ok(
        Math.abs(distance - shortest) < 0.01,
        `${link.child}: shortest corner route`,
      );
      assert.equal(x1, x2, "Adjacent tiers need only a direct vertical drop");
    }
    const selected = graph.byId.get("paragraph-3")!,
      tile = layout.tiles.find((t) => t.node.id === selected.id)!;
    const related = instanceNeighborhood(layout, tile.key);
    assert.deepEqual(
      new Set(
        layout.tiles
          .filter((t) => related.ancestors.has(t.key))
          .map((t) => t.node.id),
      ),
      new Set(["paragraph-3", "story", "purpose", "practical-care"]),
    );
    assert.deepEqual(
      instanceReelCandidates(graph, layout, selected, 2, tile.key).nodes.map(
        (n) => n.id,
      ),
      ["story", "practical-care"],
    );
    assert.equal(
      instanceReelCandidates(graph, layout, selected, 4, tile.key).ended,
      true,
    );
    const width = leaves[0].width;
    for (const leaf of leaves) {
      const v = (leaf.dotY / height) * 2 - 1;
      const t = (leaf.dotX / width - 0.46) / 0.43;
      assert.ok(
        Math.abs((1 - t) ** 2 + v * v - 1) < 1e-7,
        "Every leaf is on one continuous inset ellipse",
      );
      assert.ok(
        leaf.dotX < width * 0.92,
        "Leaf dots stay before the taper begins",
      );
    }
    assert.ok(
      layout.outline.every((d) => d.includes(" A")),
      "Exact arcs close the shared back",
    );
    for (const leaf of leaves) {
      const points = leaf.path.match(/-?\d+\.\d+,-?\d+\.\d+/g)!;
      assert.equal(
        points[0],
        points.at(-1),
        "No clipped wedge at the curved entrance",
      );
    }
  }
});

test("batch attention combines recurrence and confidence without rewarding frame duplication", async () => {
  const p = await createExample(),
    node = p.goalHierarchy!.nodes.find((n) => n.id === "paragraph-1")!;
  const frames = p.currentAttention!.filter((f) => f.span.region === "p2");
  const support = (value: number) => ({
    value,
    scale: [0, 1] as [number, number],
    semantics: "relative" as const,
    meaning: "Fixture confidence",
  });
  frames[0].items = [
    { hypothesis: "focus-0", support: support(0.6) },
    { hypothesis: "focus-1", support: support(0.95) },
  ];
  frames[1].items = [{ hypothesis: "focus-0", support: support(0.6) }];
  frames[2].items = [];
  const first = attentionForNode(p, "maker-1", node);
  assert.equal(first[0].id, "focus-0");
  assert.ok(Math.abs(first[0].support!.value - 0.4) < 1e-10);
  assert.ok(Math.abs(first[1].support!.value - 0.95 / 3) < 1e-10);
  assert.match(first[0].description, /2 of 3 selected sentences/);
  const original = frames[0],
    mid = Math.floor((original.span.start + original.span.end) / 2);
  p.currentAttention = p.currentAttention!.filter((f) => f !== original);
  p.currentAttention.push(
    { ...original, span: { ...original.span, end: mid } },
    { ...original, span: { ...original.span, start: mid } },
  );
  assert.deepEqual(attentionForNode(p, "maker-1", node), first);
});

test("supplied order uncertainty validates sibling references and preserves older contracts", async () => {
  const packet = await createExample();
  assert.equal(
    parsePacket(JSON.stringify(packet)).goalHierarchy!.orderUncertainGroups!
      .length,
    2,
  );
  const legacy = structuredClone(packet);
  legacy.schemaVersion = "1.4";
  delete legacy.ghostReadings;
  delete legacy.goalHierarchy!.orderUncertainGroups;
  assert.doesNotThrow(() => parsePacket(JSON.stringify(legacy)));
  for (const nodes of [
    ["missing", "sentence-1-1"],
    ["sentence-1-1", "sentence-2-1"],
    ["sentence-1-1", "sentence-1-1"],
  ]) {
    const bad = structuredClone(packet);
    bad.goalHierarchy!.orderUncertainGroups![0].nodes = nodes;
    assert.throws(() => parsePacket(JSON.stringify(bad)), /order uncertainty/);
  }
});

test("free context retains date meanings, creator identity, cache expiry and cancellation", async () => {
  clearContextCache();
  let requests = 0,
    now = 1000;
  const items: import("../src/core/model").ContextItem[] = [];
  const options = {
    sources: [
      { author: "Alice", url: "https://github.com/alice" },
      { author: "Bob", url: "https://github.com/bob" },
    ],
    creator: "Alice",
    useGitHub: true,
    followLinks: true,
    signal: new AbortController().signal,
    onResult: (item: (typeof items)[number]) => items.push(item),
    onProgress: () => {},
    now: () => now,
    fetcher: (async (url, init) => {
      requests++;
      assert.equal(String(url), "https://api.github.com/users/alice");
      assert.equal(init?.credentials, "omit");
      return new Response(
        JSON.stringify({
          login: "alice",
          bio: "I build gardens",
          created_at: "2019-02-01T12:00:00Z",
          updated_at: "2026-10-11T09:00:00Z",
          blog: "https://alice.example.org/about",
        }),
        { headers: { "Content-Type": "application/json" } },
      );
    }) as typeof fetch,
  };
  const first = await collectCreatorContext(options);
  assert.equal(first.collected, 1);
  assert.equal(
    first.skipped[0].reason,
    "Outside the explicitly granted source sites",
  );
  assert.equal(items[0].provenance?.author, "Alice");
  assert.equal(items[0].selected, false);
  assert.equal((await collectCreatorContext(options)).cached, 1);
  assert.equal(requests, 1);
  now += 16 * 60 * 1000;
  assert.equal((await collectCreatorContext(options)).cached, 0);
  assert.equal(requests, 2);
  const timeline = contextTimeline(items, "Alice");
  assert.deepEqual(
    timeline.dated.map((f) => f.dateKind),
    ["account-created", "profile-updated"],
  );
  assert.equal(contextTimeline(items, "Bob").sources.length, 0);
  assert.match(contextBrief(items, "Alice"), /not biographical event dates/);
  clearContextCache();
  const job = new AbortController();
  await assert.rejects(
    collectCreatorContext({
      ...options,
      signal: job.signal,
      fetcher: async () => {
        job.abort();
        return new Response("Late body", {
          headers: { "Content-Type": "text/plain" },
        });
      },
      onResult: () => assert.fail("Late context must not enter the session"),
    }),
    /cancelled/,
  );
});

test("calendar extraction keeps precision and rejects imaginary dates", () => {
  for (const date of ["2024", "2024-02", "2024-02-29"])
    assert.equal(calendarDate(date), date);
  assert.equal(calendarDate("2024-02-29T12:30:00Z"), "2024-02-29");
  for (const date of [
    "2023-02-29",
    "2024-13-01",
    "2024-00-01",
    "2024-02-30",
    "2024Tnonsense",
    "2024-02-29Tnonsense",
    "around 2024",
  ])
    assert.equal(calendarDate(date), undefined);
});

test("preference traces and directional evidence round-trip without inventing legacy data", async () => {
  const p = await createExample();
  const { demoGlobalValues } = await import("../src/core/example-values");
  const { readingHelp } = await import("../src/core/ghost");
  const values = p.hypotheses.filter((h) => h.kind === "value");
  assert.equal(values.length, 9);
  assert.ok(values.every((h) => h.support!.value < 0.25));
  const globals = demoGlobalValues(p, values);
  assert.equal(globals.length, 8);
  assert.equal(
    globals.filter((g) => values.some((v) => v.label === g.label)).length,
    4,
  );
  assert.ok(globals.every((h) => h.support!.value > 0.8));
  assert.deepEqual(
    demoGlobalValues({ ...p, origin: "live provider" }, values),
    [],
  );
  const roundTrip = parsePacket(JSON.stringify(p));
  assert.equal(
    roundTrip.hypotheses.find((h) => h.id === "care")!.preferenceTrace!
      .observations.length,
    3,
  );
  const reading = p.ghostReadings![3];
  assert.deepEqual(
    readingHelp(reading, p).evidence.map((e) => e.direction),
    ["less", "more"],
  );
  assert.ok(
    readingHelp(
      { ...reading, evidenceDirections: undefined },
      p,
    ).evidence.every((e) => e.direction === "neutral"),
  );
  const bad = structuredClone(p);
  bad.ghostReadings![0].evidenceDirections = [
    { id: "missing", direction: "more" },
  ];
  assert.throws(() => parsePacket(JSON.stringify(bad)));
  const legacy = structuredClone(p);
  legacy.ghostReadings!.forEach((g) => delete g.evidenceDirections);
  legacy.hypotheses.forEach((h) => delete h.preferenceTrace);
  assert.ok(parsePacket(JSON.stringify(legacy)));
});
