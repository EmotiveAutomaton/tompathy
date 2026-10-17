import { readFileSync } from "node:fs";
import { test } from "node:test";
import { keepsPreviewProgress } from "../src/core/preview";
import {
  localProvider,
  registryProvider,
  providerOrigin,
  checkCompanion,
  CompanionUnavailable,
} from "../src/core/provider";
import assert from "node:assert/strict";
import {
  createExample,
  exampleContext,
  exampleText,
} from "../src/core/example";
import {
  makeArtifact,
  PreferenceTraceSchema,
  PreferenceEstimateSchema,
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
  previewHierarchyLayout,
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
import { prepareContextSources } from "../src/core/creator-context";
import { exportSafe } from "../src/core/export-privacy";

test("preview exports refuse personal readings, including history, and remove local usernames", () => {
  const person = { provider: { mode: "preview" }, makers: [{ kind: "person", localLabel: "Editor Name", label: "Editor 1" }] };
  assert.throws(() => exportSafe({ history: [person] }), /stay local/);
  assert.deepEqual(exportSafe({ makers: [{ localLabel: "Editor Name", label: "Editor 1" }], detail: "Editor Name changed this." }), { makers: [{ label: "Editor 1" }], detail: "Editor 1 changed this." });
  assert.throws(() => exportSafe({ makers: person.makers, anchor: { exact: "Editor Name" } }), /anchors/);
});

test("unusual DAG shapes retain every node and finite geometry; dense graphs avoid unused SVG work", () => {
  let seed = 145;
  const random = () =>
    (seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296;
  const node = (i: number): import("../src/core/hierarchy").GoalNode => ({
    id: `n${i}`,
    maker: "m",
    label: `Node ${i}`,
    description: "Constructed graph",
    regions: ["r"],
    evidence: [],
  });
  const shapes = [
    Array.from({ length: 64 }, (_, i) => ({
      ...node(i),
      ...(i < 63 ? { parentIds: [`n${i + 1}`] } : {}),
    })),
  ];
  for (let sample = 0; sample < 40; sample++) {
    const nodes = Array.from(
      { length: 1 + Math.floor(random() * 100) },
      (_, i) => node(i),
    );
    nodes.forEach((n, i) => {
      const parents = nodes
        .slice(i + 1)
        .filter(() => random() < 0.06)
        .slice(0, 4)
        .map((p) => p.id);
      if (parents.length) n.parentIds = parents;
    });
    shapes.push(nodes);
  }
  for (const nodes of shapes) {
    const graph = goalGraph(nodes);
    for (const height of [160, 500]) {
      const layout = hierarchyLayout(graph, height);
      assert.equal(layout.tiles.length, nodes.length);
      assert.equal(
        new Set(layout.tiles.map((t) => t.node.id)).size,
        nodes.length,
      );
      for (const t of layout.tiles) {
        assert.ok(
          [t.x, t.y, t.height, t.width, t.dotX, t.dotY, t.dotHeight].every(
            Number.isFinite,
          ),
        );
        assert.doesNotMatch(t.path, /NaN|Infinity/);
        assert.ok(
          layout
            .slices(t.dotX)
            .some(([a, b]) => t.dotY >= a - 1e-7 && t.dotY <= b + 1e-7),
        );
      }
    }
  }
  const dense = hierarchyLayout(
    goalGraph(Array.from({ length: 3000 }, (_, i) => node(i))),
  );
  assert.equal(dense.dense, true);
  assert.equal(dense.outline.length, 0);
  assert.equal(dense.tiles.length, 0);
  const small = goalGraph([{ ...node(0), parentIds: ["n1"] }, node(1)]);
  assert.ok(
    hierarchyLayout(small, 0, 0, [1e308, 1e308]).edges.every(Number.isFinite),
  );
  assert.throws(
    () => goalGraph([{ ...node(0), parentIds: ["n0"] }]),
    /acyclic/,
  );
  assert.throws(() => goalGraph([node(0), node(0)]), /Duplicate/);
  assert.throws(
    () => goalGraph([{ ...node(0), parentIds: ["absent"] }]),
    /Missing/,
  );
});

test("structured estimates preserve actual units and unknown uncertainty; trajectories require ordered points", async () => {
  const estimate = {
    quantity: "Conditional coefficient",
    value: -0.8,
    reference: 0,
    interval: {
      lower: -1.2,
      upper: -0.4,
      level: 0.95,
      method: "Constructed conditional interval",
    },
    basis: "Constructed verification only",
  };
  assert.deepEqual(PreferenceEstimateSchema.parse(estimate), estimate);
  assert.equal(
    PreferenceEstimateSchema.parse({ ...estimate, interval: null }).interval,
    null,
  );
  for (const value of [NaN, Infinity, -Infinity])
    assert.equal(
      PreferenceEstimateSchema.safeParse({ ...estimate, value }).success,
      false,
    );
  assert.equal(
    PreferenceEstimateSchema.safeParse({
      ...estimate,
      interval: { ...estimate.interval, upper: -1 },
    }).success,
    false,
  );
  const packet = await createExample();
  const value = packet.hypotheses.find((h) => h.kind === "value")!;
  const trace = structuredClone(value.preferenceTrace!);
  assert.equal(
    PreferenceTraceSchema.safeParse({
      ...trace,
      points: [...trace.points].reverse(),
    }).success,
    false,
  );
  assert.equal(
    PreferenceTraceSchema.safeParse({
      ...trace,
      points: [trace.points[0], trace.points[0]],
    }).success,
    false,
  );
  assert.equal(
    PreferenceTraceSchema.parse({ ...trace, observations: [] }).observations
      .length,
    0,
  );
  delete value.preferenceTrace;
  value.preferenceEstimate = estimate;
  assert.throws(() => parsePacket(JSON.stringify(packet)), /1.8/);
  packet.schemaVersion = "1.8";
  assert.deepEqual(
    parsePacket(JSON.stringify(packet)).hypotheses.find(
      (h) => h.id === value.id,
    )!.preferenceEstimate,
    estimate,
  );
});

test("context planning isolates bad links, partial permissions and cache modes", async () => {
  clearContextCache();
  assert.equal(
    githubRepository("https://github.com/alice/repo/blob/main/%ZZ"),
    null,
  );
  const unusualSource = prepareContextSources(
    [
      { author: "Alice", url: "https://github.com/alice/repo/blob/main/%ZZ" },
      { author: "Alice", url: "https://example.org/about" },
    ],
    [],
    "Alice",
    true,
  );
  assert.ok(unusualSource.origins.includes("https://example.org"));
  const sources = [
    { author: "Alice", url: "not a URL" },
    { author: "Alice", url: "https://github.com/alice" },
    { author: "Alice", url: "https://ungranted.example.org/about" },
  ];
  const plan = prepareContextSources(
    sources,
    [
      "https://github.com/alice/repo/blob/main/%ZZ",
      "https://github.com/alice/repo",
    ],
    "Alice",
    true,
  );
  assert.equal(plan.skipped.length, 2);
  assert.deepEqual(plan.origins, [
    "https://api.github.com",
    "https://ungranted.example.org",
  ]);
  const seen: string[] = [];
  const base = {
    sources,
    creator: "Alice",
    useGitHub: true,
    followLinks: false,
    signal: new AbortController().signal,
    onResult: () => {},
    onProgress: () => {},
    allowedOrigins: ["https://api.github.com"],
    fetcher: async (url: RequestInfo | URL) => {
      seen.push(String(url));
      return new Response(
        JSON.stringify({ login: "alice", bio: "Constructed public profile" }),
        { headers: { "content-type": "application/json" } },
      );
    },
  };
  const result = await collectCreatorContext(base);
  assert.equal(result.collected, 1);
  assert.equal(result.skipped.length, 2);
  assert.deepEqual(seen, ["https://api.github.com/users/alice"]);
  assert.ok(result.skipped.some((s) => s.reason.startsWith("Source access")));
  const repo = "https://github.com/alice/repo";
  await collectCreatorContext({
    ...base,
    sources: [{ author: "Alice", url: repo }],
    useGitHub: false,
    allowedOrigins: ["https://github.com"],
    fetcher: async () =>
      new Response("Constructed repository page", {
        headers: { "content-type": "text/plain" },
      }),
  });
  let apiCalls = 0;
  const github = await collectCreatorContext({
    ...base,
    sources: [{ author: "Alice", url: repo }],
    fetcher: async (url) => {
      apiCalls++;
      return new Response(
        JSON.stringify(
          String(url).includes("/commits?")
            ? []
            : { private: false, default_branch: "main" },
        ),
        { headers: { "content-type": "application/json" } },
      );
    },
  });
  assert.equal(github.cached, 0);
  assert.equal(apiCalls, 2);
});

test("provider validation and registry fetch bind to the exact capture", async () => {
  assert.equal(providerOrigin({ kind: "none" }), null);
  for (const url of [
    "https://127.0.0.1:8765",
    "http://localhost:8765",
    "http://192.168.1.1",
    "http://127.0.0.1:8765/path",
  ])
    assert.throws(() =>
      providerOrigin({ kind: "local", url, token: "a".repeat(64) }),
    );
  assert.throws(() =>
    providerOrigin({ kind: "registry", url: "http://example.com" }),
  );
  const p = await createExample();
  const hash = createHash("sha256").update(p.artifact.id).digest("hex");
  const path = `packets/${hash}/${p.artifact.revision}.json`;
  const calls: string[] = [];
  const fake = (async (url, init) => {
    calls.push(String(url));
    assert.equal(init?.credentials, "omit");
    return Response.json(
      calls.length === 1
        ? [
            {
              artifact_id_hash: hash,
              revisions: [p.artifact.revision],
              packet_paths: { [p.artifact.revision]: path },
            },
          ]
        : p,
    );
  }) as typeof fetch;
  const request = {
    requestId: "test",
    artifact: p.artifact,
    scope: "artifact" as const,
    context: [],
    signal: new AbortController().signal,
  };
  assert.equal(
    (
      await registryProvider("https://registry.example/v1", fake).analyze(
        request,
      )
    ).id,
    p.id,
  );
  assert.deepEqual(calls, [
    `https://registry.example/v1/index/${hash.slice(0, 4)}.json`,
    `https://registry.example/v1/${path}`,
  ]);
  await assert.rejects(
    registryProvider("https://registry.example", fake).analyze({
      ...request,
      scope: "context",
    }),
    /work only/,
  );
  const changed = structuredClone(p);
  changed.artifact.title = "Different title";
  changed.artifact.regions[0].anchor.prefix = "wrong";
  await assert.rejects(
    localProvider("http://127.0.0.1:8765", "a".repeat(64), (async () =>
      Response.json(changed)) as typeof fetch).analyze(request),
  );
});

test("unreachable companion has recovery guidance without disguising server errors", async () => {
  const p = await createExample();
  const request = {
    requestId: "offline",
    artifact: p.artifact,
    scope: "artifact" as const,
    context: [],
    signal: new AbortController().signal,
  };
  const offline = localProvider(
    "http://127.0.0.1:8765",
    "b".repeat(64),
    (async () => {
      throw new TypeError("Failed to fetch");
    }) as typeof fetch,
  );
  await assert.rejects(
    offline.analyze(request),
    (e: unknown) =>
      e instanceof CompanionUnavailable &&
      /Practice ToMpathy.cmd/.test(e.message),
  );
  const unauthorized = localProvider(
    "http://127.0.0.1:8765",
    "b".repeat(64),
    (async () => new Response("", { status: 401 })) as typeof fetch,
  );
  await assert.rejects(unauthorized.analyze(request), /token was not accepted/);
});

test("local analysis sends only selected context and cancels server work", async () => {
  const p = await createExample();
  const job = new AbortController();
  const calls: { url: string; init?: RequestInit }[] = [];
  const fake = (async (url, init) => {
    calls.push({ url: String(url), init });
    if (init?.method === "DELETE") return Response.json({ cancelled: true });
    job.abort();
    throw new DOMException("Aborted", "AbortError");
  }) as typeof fetch;
  await assert.rejects(
    localProvider("http://127.0.0.1:8765", "b".repeat(64), fake).analyze({
      requestId: "request-test",
      artifact: p.artifact,
      scope: "context",
      signal: job.signal,
      context: [
        { ...exampleContext, selected: true },
        { ...exampleContext, id: "unselected", selected: false },
      ],
    }),
    /Aborted/,
  );
  assert.equal(calls.length, 2);
  assert.equal(calls[1].init?.method, "DELETE");
  const body = JSON.parse(calls[0].init!.body as string);
  assert.equal(body.context.length, 1);
  assert.equal(body.context[0].id, exampleContext.id);
  assert.equal(
    (calls[0].init?.headers as Record<string, string>).Authorization,
    `Bearer ${"b".repeat(64)}`,
  );
});

test("local engine streams bounded progress and refuses incomplete or mismatched readings", async () => {
  const packet = await createExample();
  const phases: string[] = [];
  const request = {
    requestId: "stream",
    artifact: packet.artifact,
    scope: "artifact" as const,
    context: [],
    signal: new AbortController().signal,
    onProgress: (p: string) => phases.push(p),
  };
  const stream = (text: string) => {
    const bytes = new TextEncoder().encode(text);
    return new Response(
      new ReadableStream({
        start(controller) {
          for (let i = 0; i < bytes.length; i += 73)
            controller.enqueue(bytes.slice(i, i + 73));
          controller.close();
        },
      }),
      { headers: { "content-type": "text/event-stream" } },
    );
  };
  const run = (text: string) =>
    localProvider("http://127.0.0.1:8765", "b".repeat(64), (async (
      _url,
      init,
    ) => {
      assert.equal(
        (init?.headers as Record<string, string>).Accept,
        "text/event-stream",
      );
      return stream(text);
    }) as typeof fetch).analyze(request);
  const progress =
    'event: progress\r\ndata: {"phase":"Compiling revisions 🌞"}\r\n\r\n';
  assert.equal(
    (await run(progress + `event: packet\ndata: ${JSON.stringify(packet)}\n\n`))
      .id,
    packet.id,
  );
  assert.deepEqual(phases, ["Compiling revisions 🌞"]);
  await assert.rejects(run(progress), /disconnected/);
  await assert.rejects(run("event: error\ndata: {}\n\n"), /could not complete/);
  await assert.rejects(run("x".repeat(2_500_001)), /size limit/);
  const changed = structuredClone(packet);
  changed.artifact.regions[0].anchor.exact += "tampered";
  await assert.rejects(
    run(`event: packet\ndata: ${JSON.stringify(changed)}\n\n`),
  );
});

test("companion connection check authenticates without sending a capture", async () => {
  const settings = {
    kind: "local" as const,
    url: "http://127.0.0.1:8765",
    token: "c".repeat(64),
  };
  const health = await checkCompanion(settings, (async (url, init) => {
    assert.equal(url, settings.url + "/v1/health");
    assert.equal(init?.body, undefined);
    assert.equal(
      (init?.headers as Record<string, string>).Authorization,
      `Bearer ${settings.token}`,
    );
    return Response.json({
      engineVersion: "test",
      implementationHash: "a".repeat(64),
      admittedModules: [],
      historyAvailable: ["wikipedia"],
      transcriberEnabled: false,
    });
  }) as typeof fetch);
  assert.deepEqual(health.admittedModules, []);
  await assert.rejects(
    checkCompanion(settings, (async () =>
      Response.json({}, { status: 401 })) as typeof fetch),
    /token/,
  );
});

test("engine contract preserves legacy readings and validates population evidence", async () => {
  const p = await createExample();
  p.schemaVersion = "1.7";
  const value = p.hypotheses.find((h) => h.kind === "value" && h.support)!;
  value.interpretation = "drive";
  value.icon = "care";
  p.makers[0].predictability = {
    value: 0.5,
    scale: [0, 1],
    semantics: "relative",
    meaning: "Constructed consistency fixture",
  };
  p.population = {
    populationId: "writing-fixture",
    makersPooled: 20,
    description: "Constructed writing population; no real makers",
    items: [
      {
        hypothesis: value.id,
        populationSupport: { ...value.support! },
        makerRecords: 0,
        shrinkage: 0,
        curve: [
          { records: 0, intervalWidth: 1 },
          { records: 10, intervalWidth: 0.5 },
        ],
      },
    ],
  };
  assert.equal(parsePacket(JSON.stringify(p)).population!.makersPooled, 20);
  for (const change of [
    (q: typeof p) => {
      q.schemaVersion = "1.6";
    },
    (q: typeof p) => {
      q.population!.items[0].hypothesis = "absent";
    },
    (q: typeof p) => {
      q.population!.items[0].shrinkage = 0.1;
    },
    (q: typeof p) => {
      q.population!.items[0].populationSupport.value = 200;
    },
    (q: typeof p) => {
      q.population!.items[0].populationSupport.semantics = "probability";
    },
    (q: typeof p) => {
      q.population!.items[0].curve.reverse();
    },
    (q: typeof p) => {
      q.makers[0].predictability!.semantics = "probability";
    },
  ]) {
    const invalid = structuredClone(p);
    change(invalid);
    assert.throws(() => parsePacket(JSON.stringify(invalid)));
  }
  assert.ok(parsePacket(JSON.stringify(await createExample())));
});

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
  assert.equal(values.length, 16);
  assert.equal(values.filter(h => h.valueCategory === "drive" && h.support === null).length, 7);
  assert.ok(values.filter(h => h.valueCategory === "constructed").every((h) => h.support!.value < 0.25));
  const globals = demoGlobalValues(p, values);
  assert.equal(globals.length, 15);
  assert.equal(
    globals.filter((g) => values.some((v) => v.label === g.label)).length,
    11,
  );
  assert.equal(globals.filter(h => h.valueCategory === "drive" && h.support === null).length, 7);
  assert.ok(globals.filter(h => h.support).every((h) => h.support!.value > 0.8));
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


test("preview geometry reserves source groups without inventing inferred nodes", () => {
  for (const count of [1, 2, 20]) {
    const groups = Array.from({ length: count }, (_, i) => [`p${i}`]);
    const nodes = groups.map((regions, i) => ({ id: `g${i}`, maker: "fixture", regions, evidence: [], label: "Fixture", description: "Software fixture", level: "paragraph" as const }));
    const empty = previewHierarchyLayout(goalGraph([]), groups, 250, 320);
    const first = previewHierarchyLayout(goalGraph(nodes.slice(0, 1)), groups, 250, 320);
    const full = previewHierarchyLayout(goalGraph([...nodes, { id: "cover", maker: "fixture", regions: groups.flat(), evidence: [], label: "Cover fixture", description: "Software fixture", level: "document" }]), groups, 250, 320);
    assert.equal(empty.tiles.length, 0);
    assert.equal(first.tiles.length, 1);
    assert.equal(full.tiles.length, count + 1);
    assert.deepEqual(empty.outline, full.outline);
    assert.deepEqual(first.outline, full.outline);
    assert.equal(first.tiles[0].dotY, full.tiles.find(t => t.node.id === "g0")!.dotY);
    assert.equal(full.tiles.some(t => t.node.id.startsWith("layout-only:")), false);
    assert.equal(full.links.length, 0);
  }
});

test("preview continuation retains completed evidence until replay catches up", async () => {
  const previous = await createExample();
  previous.preview = { readers: [], coverage: ["p1"], modules: [{ id: "goals", title: "Goals", status: "complete", detail: "Fixture", completed: 3, total: 3 }] };
  const replay = structuredClone(previous);
  replay.preview!.modules[0].status = "running";
  assert.equal(keepsPreviewProgress(replay, previous), false);
  replay.preview!.modules[0].status = "complete";
  replay.preview!.coverage = [];
  assert.equal(keepsPreviewProgress(replay, previous), false);
  replay.preview!.coverage = ["p1", "p2"];
  assert.equal(keepsPreviewProgress(replay, previous), true);
});

test("compact preview streams merge and validate every patch", async () => {
  const packet = await createExample();
  packet.provider.mode = "preview";
  packet.provider.previewNotice = "Constructed software fixture; not a real reading.";
  for (const item of [...packet.hypotheses, ...(packet.goalHierarchy?.nodes ?? []), ...(packet.currentAttention ?? []).flatMap(f => f.items)]) {
    item.evidenceStatus = "unvalidated";
    item.basis = "model-judgment";
  }
  packet.preview = { readers: [], modules: [] };
  const seen: typeof packet[] = [];
  const request = { requestId: "compact", artifact: packet.artifact, scope: "artifact" as const, context: [], mode: "preview" as const, signal: new AbortController().signal, onPartial: (p: typeof packet) => seen.push(p) };
  const event = (name: string, data: unknown) => `event: ${name}\ndata: ${JSON.stringify(data)}\n\n`;
  const run = (events: string) => localProvider("http://127.0.0.1:8765", "b".repeat(64), (async () => new Response(events, { headers: { "content-type": "text/event-stream" } })) as typeof fetch).analyze(request);
  const updated = { ...packet.preview, resumable: true, coverage: [packet.artifact.regions[0].id] };
  await run(event("partial", packet) + event("partial-update", { preview: updated }) + event("packet", { ...packet, preview: updated }));
  assert.equal(seen.length, 2);
  assert.equal(seen[1].preview!.resumable, true);
  await assert.rejects(run(event("partial-update", { preview: updated })), /initial|first|before/i);
  await assert.rejects(run(event("partial", packet) + event("partial-update", { artifact: { ...packet.artifact, revision: "wrong" } })), /./);
});


test("preview parsing preserves engine fields and refuses nested unknowns", () => {
  const raw = JSON.parse(readFileSync("engine/tests/fixtures/packets/preview-entries.json", "utf8"));
  assert.deepEqual(parsePacket(JSON.stringify(raw)), raw);
  for (const mutate of [
    (p: any) => { p.preview.newEngineField = true; },
    (p: any) => { p.hypotheses[0].unrecognized = "must not disappear"; },
    (p: any) => { p.artifact.regions[0].anchor.unrecognized = 1; },
    (p: any) => { p.globalFindings[0].unrecognized = 1; },
  ]) {
    const changed = structuredClone(raw);
    mutate(changed);
    assert.throws(() => parsePacket(JSON.stringify(changed)), /Unknown preview field/);
  }
});
import { markedAINodes, aiOutlineOpacity, aiOutlineWidth } from "../src/core/ai-attribution";
test("AI outlines require distinct attribution, calibration and a strict majority", async () => {
  const packet = await createExample();
  const nodes = packet.goalHierarchy!.nodes;
  const illustrative = markedAINodes(packet);
  assert.equal(illustrative.size, 3);
  for (const [id, mark] of illustrative) {
    const node = nodes.find(n => n.id === id)!;
    const reading = packet.ghostReadings!.find(r => r.span.region === node.span!.region && r.span.start === node.span!.start)!;
    assert.equal(mark.confidence, reading.confidence);
    assert.equal(mark.involvement, reading.kind);
  }
  assert.ok(aiOutlineWidth("edited") < aiOutlineWidth("curated"));
  assert.ok(aiOutlineWidth("curated") < aiOutlineWidth("ghost"));
  assert.ok(aiOutlineOpacity(.6) < aiOutlineOpacity(.8));
  assert.ok(aiOutlineOpacity(.8) < aiOutlineOpacity(1));
  // The authored display levels must never leak onto ordinary reading packets.
  packet.provider.id = "test-other-provider";
  assert.deepEqual([...markedAINodes(packet).keys()], ["sentence-6-3"]);
  const node = nodes.find(n => n.id === "sentence-6-3")!;
  node.aiAttribution = { basis: "calibrated", probability: .5, calibration: "known-answer calibration fixture", evidence: ["production-ghost"] };
  assert.equal(markedAINodes(packet).size, 0);
  node.aiAttribution.probability = .501;
  assert.equal(markedAINodes(packet).size, 1);
  assert.equal(markedAINodes(packet, "different-maker").size, 0);
  const invalid = structuredClone(packet);
  invalid.goalHierarchy!.nodes.find(n => n.id === node.id)!.aiAttribution!.evidence = ["missing"];
  assert.throws(() => parsePacket(JSON.stringify(invalid)));
});
