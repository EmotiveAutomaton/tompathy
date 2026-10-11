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
import { publicURL, retrieve, collectSources } from "../src/core/collector";
import { acceptRevision, analysisHandoff } from "../src/core/reading";
import { contextIdentity, mergeContext } from "../src/core/context";
import { createHash } from "node:crypto";
import { goalAt, goalTree } from "../src/core/hierarchy";
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
  const tree = goalTree(nodes)!;
  const paragraph = tree.descendants().find((n) => n.id === "paragraph-3")!;
  assert.equal(paragraph.descendants().length, 5);
  assert.deepEqual(
    paragraph.ancestors().map((n) => n.id),
    ["paragraph-3", "story", "purpose"],
  );
  const legacy = structuredClone(packet);
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
  p.hypotheses[0].support!.value = 0;
  assert.equal(parsePacket(JSON.stringify(p)).hypotheses[0].support?.value, 0);
  p.hypotheses[0].support!.value = 2;
  assert.throws(() => parsePacket(JSON.stringify(p)), /outside declared scale/);
  p.hypotheses[0].support = null;
  p.hypotheses[0].evidence = ["missing"];
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
  assert.equal(p.schemaVersion, "1.2");
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
  const p = await createExample();
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
