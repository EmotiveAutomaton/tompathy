import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  ArrowDownLeft,
  ArrowRight,
  BookOpen,
  Check,
  ChevronRight,
  CircleHelp,
  Download,
  Expand,
  GitBranch,
  Layers,
  Link,
  LoaderCircle,
  MoreHorizontal,
  MousePointer2,
  Pin,
  Plus,
  RefreshCw,
  Search,
  Settings2,
  Sparkles,
  Sun,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import {
  type Packet,
  type Hypothesis,
  type ContextItem,
  type Scope,
  type Session,
  SessionSchema,
  makeArtifact,
  matchPacket,
  parsePacket,
} from "./core/model";
import { createExample, exampleContext, exampleText } from "./core/example";
import { collectSources, publicURL } from "./core/collector";
import {
  acceptRevision,
  analysisHandoff,
  contributionExplanation,
  interpretationLabel,
} from "./core/reading";
import { contextIdentity, mergeContext } from "./core/context";
import {
  capturePage,
  captureSelection,
  isExtension,
  pageCommand,
  markPage,
  readSession,
  writeSession,
  readTheme,
  writeTheme,
  download,
} from "./browser";

export function Brand() {
  return (
    <div className="brand">
      <span className="brand-symbol" aria-hidden="true">
        <i />
        <i />
        <i />
      </span>
      <div>
        <strong>
          ToMpathy<span className="brand-dot">.</span>
        </strong>
        <small>Maker Reader</small>
      </div>
    </div>
  );
}
function IconButton({
  label,
  onClick,
  children,
}: {
  label: string;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      className="icon-button"
      aria-label={label}
      title={label}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const prior = document.activeElement as HTMLElement;
    const fit = () => {
      if (!ref.current) return;
      const zoom =
        Number.parseFloat(getComputedStyle(document.documentElement).zoom) || 1;
      ref.current.style.maxHeight = `${Math.max(120, ((visualViewport?.height ?? innerHeight) - 24) / zoom)}px`;
      ref.current.style.maxWidth = `${Math.max(120, ((visualViewport?.width ?? innerWidth) - 24) / zoom)}px`;
    };
    fit();
    window.addEventListener("resize", fit);
    visualViewport?.addEventListener("resize", fit);
    ref.current?.showModal();
    return () => {
      window.removeEventListener("resize", fit);
      visualViewport?.removeEventListener("resize", fit);
      prior?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className="modal"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <header>
        <h2>{title}</h2>
        <IconButton label="Close dialog" onClick={onClose}>
          <X size={19} />
        </IconButton>
      </header>
      <div className="modal-body">{children}</div>
    </dialog>
  );
}
const empty: Session = {
  sessionVersion: "1.0",
  artifact: null,
  packet: null,
  scope: "artifact",
  context: [],
};
export function App({ preview = false }: { preview?: boolean }) {
  const [session, setSession] = useState<Session>(empty),
    [hydrated, setHydrated] = useState(false),
    [tabId, setTabId] = useState<number | null>(null),
    [region, setRegion] = useState("p2"),
    [pinned, setPinned] = useState(false),
    [busy, setBusy] = useState(false),
    [stale, setStale] = useState(false),
    [notice, setNotice] = useState(""),
    [error, setError] = useState(""),
    [view, setView] = useState<"tree" | "list" | "cloud">("tree"),
    [maker, setMaker] = useState(""),
    [detail, setDetail] = useState<Hypothesis | null>(null),
    [modal, setModal] = useState<
      | "menu"
      | "context"
      | "source"
      | "settings"
      | "import"
      | "help"
      | "revision"
      | "history"
      | null
    >(null),
    [theme, setTheme] = useState("system"),
    [pending, setPending] = useState<Packet | null>(null),
    [importText, setImportText] = useState(""),
    [paste, setPaste] = useState(""),
    [urls, setUrls] = useState(""),
    [contextPaste, setContextPaste] = useState(""),
    [contextSource, setContextSource] = useState("Pasted excerpt"),
    [collecting, setCollecting] = useState(false),
    [collectionStatus, setCollectionStatus] = useState<string[]>([]);
  const serial = useRef(0),
    collector = useRef<AbortController | null>(null),
    port = useRef<chrome.runtime.Port | null>(null),
    current = useRef({ session, tabId });
  current.current = { session, tabId };
  const { artifact, packet, scope, context } = session;
  const mismatch =
    packet && artifact ? matchPacket(packet, artifact, scope, context) : null;
  const ready = !!packet && !mismatch && !stale;
  const activeMaker =
    packet?.makers.find((m) => m.id === maker) ?? packet?.makers[0];
  const authorName =
    (ready && activeMaker?.identity !== "unknown"
      ? activeMaker?.label
      : null) ||
    session.authorLabel ||
    (artifact?.authors?.length === 1 ? artifact.authors[0].label : null) ||
    (artifact?.authors?.length
      ? "Multiple authors listed"
      : "Author not identified");
  const hypotheses = ready
    ? packet!.hypotheses.filter((h) => h.makers.includes(activeMaker!.id))
    : [];
  const goals = hypotheses
    .filter(
      (h) =>
        h.kind === "goal" && (!h.regions.length || h.regions.includes(region)),
    )
    .sort((a, b) => supportWeight(b) - supportWeight(a));
  const processes = hypotheses.filter(
    (h) =>
      h.kind === "process" && (!h.regions.length || h.regions.includes(region)),
  );
  const values = hypotheses.filter(
    (h) => h.kind === "value" && h.status !== "unknown",
  );
  const focus = processes
    .filter((h) => h.status !== "unknown")
    .sort((a, b) => supportWeight(b) - supportWeight(a))[0];
  const estimate = ready
    ? packet?.estimates.find((e) => e.region === region)
    : null;
  const isExample = packet?.origin === "synthetic example";
  const detailEvidence = [
    ...new Set([
      ...(detail?.evidence ?? []),
      ...(detail?.kind === "process"
        ? (packet?.process.edges
            .filter((e) => e.from === detail.id || e.to === detail.id)
            .flatMap((e) => e.evidence ?? []) ?? [])
        : []),
    ]),
  ];
  function cancelWork() {
    serial.current++;
    collector.current?.abort();
    setCollecting(false);
    setBusy(false);
    setPending(null);
  }
  async function capture() {
    cancelWork();
    const request = serial.current;
    setBusy(true);
    setError("");
    setStale(false);
    setDetail(null);
    await pageCommand(
      current.current.tabId,
      current.current.session.artifact,
      "TOMPATHY_CLEANUP",
    );
    try {
      const result = await capturePage();
      if (request !== serial.current) return;
      setTabId(result.tabId);
      setRegion(result.artifact.regions[0].id);
      setPinned(false);
      const previous = current.current.session;
      let resultPacket: Packet | null =
        previous.packet &&
        matchPacket(
          previous.packet,
          result.artifact,
          previous.scope,
          previous.context,
        ) === null
          ? previous.packet
          : null;
      if (
        !resultPacket &&
        result.artifact.source === chrome.runtime.getURL("example.html")
      ) {
        const candidate = await createExample(result.artifact.source);
        if (!matchPacket(candidate, result.artifact, "artifact", []))
          resultPacket = candidate;
      }
      if (request !== serial.current) return;
      setSession({
        sessionVersion: "1.0",
        artifact: result.artifact,
        packet: resultPacket,
        scope: resultPacket?.scope.kind ?? "artifact",
        context: resultPacket?.scope.kind === "context" ? previous.context : [],
        history: resultPacket ? previous.history : [],
        authorLabel:
          previous.artifact?.id === result.artifact.id
            ? previous.authorLabel
            : undefined,
      });
    } catch (e) {
      if (request !== serial.current) return;
      setTabId(null);
      setSession(empty);
      setError((e as Error).message);
    } finally {
      if (request === serial.current) setBusy(false);
    }
  }
  async function example() {
    cancelWork();
    setError("");
    setModal(null);
    setStale(false);
    setPinned(false);
    setRegion("p2");
    if (isExtension) {
      const tab = await chrome.tabs.create({
        url: chrome.runtime.getURL("example.html"),
      });
      setTabId(tab.id ?? null);
      const p = await createExample(chrome.runtime.getURL("example.html"));
      setSession({ ...empty, artifact: p.artifact, packet: p });
      setNotice("Move across the example text to explore.");
    } else {
      const p = await createExample();
      setSession({ ...empty, artifact: p.artifact, packet: p });
    }
  }
  useEffect(() => {
    let alive = true;
    (async () => {
      const saved = SessionSchema.safeParse(await readSession());
      if (alive && saved.success) setSession(saved.data);
      const t = await readTheme();
      if (alive) {
        setTheme(t);
        setHydrated(true);
      }
    })();
    return () => {
      alive = false;
      cancelWork();
    };
  }, []);
  useEffect(() => {
    if (hydrated)
      void writeSession(session).catch(() =>
        setError(
          "This reading could not be saved in browser session storage. Save a session file before closing the panel.",
        ),
      );
  }, [session, hydrated]);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  useEffect(() => {
    if (!hydrated) return;
    if (isExtension) void capture();
    else if (!current.current.session.artifact) void example();
  }, [hydrated]);
  useEffect(() => {
    if (!isExtension) return;
    const connect = () => {
      port.current = chrome.runtime.connect({ name: "tompathy-panel" });
      if (current.current.tabId)
        port.current.postMessage({
          type: "TRACK",
          tabId: current.current.tabId,
        });
    };
    connect();
    const receive = (m: any, sender: chrome.runtime.MessageSender) => {
      if (m.type === "TOMPATHY_INVOKED") {
        void capture();
        return;
      }
      const c = current.current;
      const sourceTab =
        sender.tab?.id ??
        (sender.id === chrome.runtime.id ? m.sourceTabId : undefined);
      if (
        sourceTab !== c.tabId ||
        m.documentId !== c.session.artifact?.id ||
        m.revision !== c.session.artifact?.revision
      )
        return;
      if (m.type === "TOMPATHY_SELECT") {
        setRegion(m.region);
        setPinned(m.pinned);
        setDetail(null);
      }
      if (m.type === "TOMPATHY_STALE") {
        cancelWork();
        setStale(true);
        setDetail(null);
      }
    };
    const changed = () => {
      cancelWork();
      void pageCommand(
        current.current.tabId,
        current.current.session.artifact,
        "TOMPATHY_CLEANUP",
      );
      setSession(empty);
      setDetail(null);
      setPinned(false);
      setTabId(null);
      void capture();
    };
    const updated = (id: number, change: { status?: string }) => {
      if (change.status === "loading" && id === current.current.tabId) {
        cancelWork();
        setStale(true);
        setDetail(null);
      }
      if (change.status === "complete")
        void chrome.tabs
          .query({ active: true, currentWindow: true })
          .then(([tab]) => {
            if (tab?.id === id) void capture();
          });
    };
    chrome.runtime.onMessage.addListener(receive);
    chrome.tabs.onActivated.addListener(changed);
    chrome.tabs.onUpdated.addListener(updated);
    return () => {
      chrome.runtime.onMessage.removeListener(receive);
      chrome.tabs.onActivated.removeListener(changed);
      chrome.tabs.onUpdated.removeListener(updated);
      port.current?.disconnect();
    };
  }, []);
  useEffect(() => {
    if (tabId && port.current) {
      try {
        port.current.postMessage({ type: "TRACK", tabId });
      } catch {
        port.current = chrome.runtime.connect({ name: "tompathy-panel" });
        port.current.postMessage({ type: "TRACK", tabId });
      }
    }
  }, [tabId]);
  useEffect(() => {
    void markPage(tabId, artifact, ready ? packet : null);
  }, [tabId, artifact, packet, ready]);
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setPinned(false);
        void pageCommand(tabId, artifact, "TOMPATHY_RELEASE");
      }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [tabId, artifact]);
  const move = (id: string, pin = false) => {
    if (pinned && !pin) return;
    setRegion(id);
    if (pin) {
      setPinned(true);
      void pageCommand(tabId, artifact, "TOMPATHY_FOCUS", { region: id });
    }
    setDetail(null);
  };
  const inspect = (h: Hypothesis) => {
    setDetail(h);
    void pageCommand(tabId, artifact, "TOMPATHY_RELATED", {
      regions: h.regions,
    });
  };
  const loadPacket = async (text: string) => {
    try {
      const p = parsePacket(text);
      if (p.origin !== "synthetic example") p.origin = "imported";
      if (!artifact)
        throw Error(
          "Capture or paste the matching artifact before importing a result.",
        );
      const reason = matchPacket(p, artifact, scope, context);
      if (reason) throw Error(reason);
      if (packet) {
        setPending(p);
        setModal("revision");
      } else {
        setSession((s) => ({ ...s, packet: p }));
        setModal(null);
      }
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const readFile = async (
    file: File | undefined,
    kind: "packet" | "session" | "context",
  ) => {
    if (!file) return;
    try {
      if (file.size > (kind === "context" ? 32000 : 2000000))
        throw Error(
          "File is too large. Context limit: 32 KB; JSON limit: 2 MB.",
        );
      const request = serial.current;
      const text = await file.text();
      if (request !== serial.current) return;
      if (kind === "packet") await loadPacket(text);
      if (kind === "session") {
        const loaded = SessionSchema.parse(JSON.parse(text));
        cancelWork();
        await pageCommand(tabId, artifact, "TOMPATHY_CLEANUP");
        setTabId(null);
        setSession({
          ...loaded,
          context: loaded.context.map((c) => ({ ...c, selected: false })),
        });
        setStale(false);
        setRegion(loaded.artifact?.regions[0].id ?? "p1");
        setModal(null);
        setNotice(
          "Session loaded as a detached snapshot. Select imported context explicitly.",
        );
      }
      if (kind === "context") addContext(text, file.name, "file");
    } catch (e) {
      setError((e as Error).message);
    }
  };
  async function addContext(
    excerpt: string,
    source: string,
    lineage: ContextItem["lineage"] = "pasted",
  ) {
    if (!excerpt.trim()) {
      setError("Add an excerpt first.");
      return;
    }
    if (context.length >= 30) {
      setError("Remove a context item before adding more (30 maximum).");
      return;
    }
    const request = serial.current;
    const text = excerpt.trim().slice(0, 20000);
    const id = await contextIdentity(source, text);
    if (request !== serial.current) return;
    setSession((s) => ({
      ...s,
      context: mergeContext(s.context, {
        id,
        source,
        excerpt: text,
        retrievedAt: new Date().toISOString(),
        lineage,
        selected: false,
      }),
    }));
    setContextPaste("");
    setError("");
  }
  async function collect() {
    setError("");
    setCollectionStatus([]);
    let selected: URL[];
    try {
      selected = urls
        .split("\n")
        .map((x) => x.trim())
        .filter(Boolean)
        .map(publicURL);
      if (selected.length < 1 || selected.length > 3)
        throw Error("Enter one to three URLs, one per line.");
      if (isExtension) {
        const allowed = await chrome.permissions.request({
          origins: selected.map((u) => `${u.origin}/*`),
        });
        if (!allowed)
          throw Error("Source access was declined. Paste an excerpt instead.");
      }
    } catch (e) {
      setError((e as Error).message);
      return;
    }
    const job = new AbortController();
    collector.current = job;
    const request = serial.current;
    setCollecting(true);
    try {
      await collectSources(
        selected!.map((u) => u.href),
        job.signal,
        (item) => {
          if (request !== serial.current || job.signal.aborted) return;
          if ("error" in item)
            setCollectionStatus((s) => [...s, `${item.source}: ${item.error}`]);
          else {
            setSession((s) => ({
              ...s,
              context: mergeContext(s.context, item),
            }));
            setCollectionStatus((s) => [
              ...s,
              `Retrieved ${item.source}. Select it to include in scope.`,
            ]);
          }
        },
      );
    } catch (e) {
      if (request === serial.current)
        setCollectionStatus((s) => [...s, (e as Error).message]);
    } finally {
      if (request === serial.current) setCollecting(false);
    }
  }
  async function revision() {
    const p = await createExample(artifact?.source, true);
    setPending(p);
    setModal("revision");
  }
  const token = (h: Hypothesis, i: number, mode = "cloud") => (
    <button
      key={h.id}
      className={`hypothesis ${mode} ${h.support == null ? "unquantified" : ""} ${i === 0 && h.support != null ? "primary-word" : ""}`}
      title={`${h.status}: ${h.description}`}
      style={
        mode === "cloud"
          ? {
              fontSize: `${h.support ? 16 + Math.max(0, Math.min(1, (h.support.value - h.support.scale[0]) / (h.support.scale[1] - h.support.scale[0]))) * 13 : 16}px`,
            }
          : undefined
      }
      onClick={() => inspect(h)}
    >
      <span>{h.label}</span>
      {mode === "list" && (
        <span className="muted">
          {h.status === "unknown"
            ? "Unresolved"
            : h.support?.semantics === "probability"
              ? `${Math.round(h.support.value * 100)}%`
              : "Inspect"}{" "}
          <ChevronRight size={13} />
        </span>
      )}
    </button>
  );
  return (
    <div className={preview ? "workspace" : "extension-root"}>
      {preview && (
        <ExampleArticle
          active={region}
          pinned={pinned}
          related={detail?.regions ?? []}
          onMove={move}
        />
      )}
      <div className="reader" data-tompathy-ui>
        <header className="app-header">
          <div className="author-identity">
            <span className="author-caption">Author</span>
            <button
              className="author-name"
              onClick={() => setModal("source")}
              title="Author and source"
            >
              {authorName}
            </button>
            <span className="identity-note">
              {busy
                ? "Capturing…"
                : isExample
                  ? "Synthetic example"
                  : ready
                    ? "Revisable account"
                    : artifact
                      ? "Awaiting analysis"
                      : "Choose a text to begin"}
            </span>
          </div>
          <Brand />
          <IconButton label="Reader menu" onClick={() => setModal("menu")}>
            <MoreHorizontal size={21} />
          </IconButton>
        </header>
        <div className={`reader-content ${ready ? "is-ready" : ""}`}>
          {error && (
            <div className="message error" role="alert">
              <span>{error}</span>
              <IconButton label="Dismiss error" onClick={() => setError("")}>
                <X size={15} />
              </IconButton>
            </div>
          )}
          {notice && (
            <div className="message" role="status">
              <span>{notice}</span>
              <IconButton label="Dismiss notice" onClick={() => setNotice("")}>
                <X size={15} />
              </IconButton>
            </div>
          )}
          {(stale || mismatch) && (
            <div className="message warning" role="status">
              <div>
                <strong>
                  {stale
                    ? "The source text changed"
                    : "A different evidence scope"}
                </strong>
                <p>
                  {stale
                    ? "Capture again to resolve the passages before viewing estimates."
                    : mismatch}
                </p>
                <button
                  className="text-button"
                  onClick={() => (stale ? void capture() : setModal("import"))}
                >
                  {stale ? "Recapture page" : "Import matching analysis"}{" "}
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          )}
          {!ready && !busy && !stale && !mismatch && (
            <section className="welcome">
              <div className="welcome-orbit">
                <Search size={24} />
              </div>
              <h2>
                {artifact
                  ? "Ready for an account"
                  : "Start with a piece of writing"}
              </h2>
              <p>
                {artifact
                  ? "Maker estimates are awaiting an analysis source. Import a result for this capture, or explore the example."
                  : "Explore possible goals, the process behind them, and the values that may connect them."}
              </p>
              <button className="primary-button" onClick={() => void example()}>
                <Sparkles size={16} /> Explore an example{" "}
                <ArrowRight size={16} />
              </button>
              <button
                className="secondary-button"
                onClick={() => setModal(artifact ? "import" : "source")}
              >
                {artifact ? "Import analysis" : "Paste a text"}
                <Upload size={15} />
              </button>
            </section>
          )}
          <section
            className="region goals-region"
            aria-labelledby="goals-title"
          >
            <div className="section-heading">
              <h2 id="goals-title">Goals</h2>
              <span
                className="section-aside"
                title="Governing purposes and local goals may coexist. Word size shows support within a declared set."
              >
                possible aims
              </span>
            </div>
            <div
              className={`goal-cloud ${view === "list" ? "as-list" : ""}`}
              data-testid="goals"
            >
              {goals.length ? (
                goals.map((h, i) =>
                  token(h, i, view === "list" ? "list" : "cloud"),
                )
              ) : (
                <p className="empty-region">
                  {ready
                    ? "No goals for this passage."
                    : "Possible aims will appear here."}
                </p>
              )}
            </div>
          </section>
          <section
            className="region process-region"
            aria-labelledby="process-title"
          >
            <div className="section-heading">
              <h2 id="process-title">Process</h2>
              <button
                className="view-toggle"
                aria-label={
                  view === "cloud"
                    ? "Collapse to process tree"
                    : "Expand process into word cloud"
                }
                aria-pressed={view === "cloud"}
                onClick={() => setView(view === "cloud" ? "tree" : "cloud")}
              >
                {view === "cloud" ? (
                  <GitBranch size={14} />
                ) : (
                  <Expand size={14} />
                )}
                {view === "cloud" ? "Tree" : "Expand"}
              </button>
            </div>
            {ready && (
              <p className="process-caption">
                {packet!.process.interpretation === "historical-production"
                  ? "Possible production history · order may be unresolved"
                  : "Process account · historical order not established"}
              </p>
            )}
            <div className={`process-map ${view}`} data-testid="process">
              {processes.length ? (
                view === "tree" ? (
                  <ProcessTree
                    nodes={hypotheses.filter(
                      (h) =>
                        h.kind === "process" &&
                        h.interpretation !== "reader-route" &&
                        h.interpretation !== "repertoire",
                    )}
                    edges={packet!.process.edges}
                    focus={focus?.id}
                    local={processes.map((h) => h.id)}
                    onInspect={inspect}
                  />
                ) : (
                  processes
                    .filter(
                      (h) =>
                        h.interpretation !== "reader-route" &&
                        h.interpretation !== "repertoire",
                    )
                    .map((h, i) => token(h, i, view))
                )
              ) : (
                <p className="empty-region">
                  {ready
                    ? "No process account for this passage."
                    : "The shape of a process will appear here."}
                </p>
              )}
            </div>
          </section>
        </div>
        {detail && (
          <Modal
            title={detail.label}
            onClose={() => {
              setDetail(null);
              void pageCommand(tabId, artifact, "TOMPATHY_RELATED", {
                regions: [],
              });
            }}
          >
            <section
              className="evidence-panel"
              aria-label="Hypothesis evidence"
            >
              <span className="eyebrow">
                {detail.status} · {detail.kind}
              </span>
              <p>{detail.description}</p>
              <p className="muted">{interpretationLabel(detail)}</p>
              {detail.support ? (
                <p className="support-line">
                  {detail.support.semantics === "probability"
                    ? `${(detail.support.value * 100).toFixed(0)}% probability`
                    : `Support ${detail.support.value} on ${detail.support.scale.join("–")}`}
                  . {detail.support.meaning}{" "}
                  {detail.support.calibration ?? "Calibration not supplied."}
                </p>
              ) : (
                <p className="support-line">Support is unquantified.</p>
              )}
              <p className="muted">
                Maker: {activeMaker?.label} · {activeMaker?.relationship}
              </p>
              {packet!.alternatives
                .filter((a) => a.members.includes(detail.id))
                .map((a) => (
                  <p className="muted" key={a.id}>
                    {a.kind === "competing"
                      ? "Competing account with"
                      : "Can coexist with"}
                    :{" "}
                    {a.members
                      .filter((id) => id !== detail.id)
                      .map(
                        (id) =>
                          packet!.hypotheses.find((h) => h.id === id)!.label,
                      )
                      .join(", ") || "no other supplied accounts"}
                    .
                    {a.exhaustive
                      ? " Complete candidate set."
                      : " Other accounts may be possible."}
                    {a.kind !== "competing" &&
                      " Coexistence does not imply statistical independence."}
                  </p>
                ))}
              {detail.kind === "process" &&
                packet!.process.edges
                  .filter((e) => e.from === detail.id || e.to === detail.id)
                  .map((e, i) => (
                    <p className="muted" key={i}>
                      {packet!.hypotheses.find((h) => h.id === e.from)!.label} →{" "}
                      {packet!.hypotheses.find((h) => h.id === e.to)!.label}:{" "}
                      {e.relationship}.{" "}
                      {e.kind
                        ? `Relationship: ${e.kind}.`
                        : "Order unspecified."}{" "}
                      {e.status ?? "hypothesis"}.
                    </p>
                  ))}
              {packet!.accounts
                ?.filter((a) => a.members.includes(detail.id))
                .map((a) => (
                  <details key={a.id}>
                    <summary>{a.label}</summary>
                    <p>{a.explanation}</p>
                    <p className="muted">
                      Compatible hypotheses:{" "}
                      {a.members
                        .map(
                          (id) =>
                            packet!.hypotheses.find((h) => h.id === id)!.label,
                        )
                        .join(" · ")}
                    </p>
                  </details>
                ))}
              {detailEvidence.length ? (
                detailEvidence.map((id) => {
                  const e = packet!.evidence.find((e) => e.id === id)!;
                  return (
                    <blockquote key={id}>
                      <p>“{e.excerpt}”</p>
                      <cite>
                        <SourceLink source={e.source} /> ·{" "}
                        {new Date(e.capturedAt).toLocaleDateString()}
                      </cite>
                      <small>{e.relationship}</small>
                    </blockquote>
                  );
                })
              ) : (
                <p className="muted">
                  No evidence was supplied for this unresolved account.
                </p>
              )}
              <div className="source-links">
                {detail.regions.map((id) => (
                  <button key={id} onClick={() => move(id, true)}>
                    <ArrowDownLeft size={13} /> Passage{" "}
                    {artifact!.regions.findIndex((r) => r.id === id) + 1}
                  </button>
                ))}
              </div>
            </section>
          </Modal>
        )}
        <section
          className="region values-region"
          aria-labelledby="values-title"
        >
          <div className="section-heading">
            <div>
              <h2 id="values-title">Values</h2>
            </div>
            <span
              className="section-aside"
              title="Values stay steady until you accept a new analysis revision."
            >
              across the text
            </span>
          </div>
          <div className="values" data-testid="values">
            {values.length ? (
              values.map((h, i) => (
                <button key={h.id} onClick={() => inspect(h)}>
                  <span
                    className={`value-symbol value-${i % 3}`}
                    aria-hidden="true"
                  >
                    {["◌", "✳", "◇"][i % 3]}
                  </span>
                  <span>
                    {h.label}
                    <small className="value-kind">
                      {h.interpretation === "preference"
                        ? "Preference"
                        : h.interpretation === "value"
                          ? "Value hypothesis"
                          : "Interpretation unspecified"}
                    </small>
                  </span>
                  <span className="value-track">
                    <i
                      style={{
                        width: h.support
                          ? `${(100 * (h.support.value - h.support.scale[0])) / (h.support.scale[1] - h.support.scale[0])}%`
                          : "0%",
                      }}
                    />
                  </span>
                </button>
              ))
            ) : (
              <p className="empty-region">
                {ready
                  ? "Not enough evidence for this author’s values."
                  : "A stable maker-level snapshot will appear here."}
              </p>
            )}
          </div>
        </section>
        <footer className="app-footer">
          {ready ? (
            <div className="passage-strip">
              <button
                className="passage-info"
                onClick={() => setModal("source")}
                title={contributionExplanation(packet!, region)}
              >
                {pinned ? "Pinned" : "Following"} passage{" "}
                {Math.max(
                  1,
                  artifact!.regions.findIndex((r) => r.id === region) + 1,
                )}
              </button>
              <button
                className="pin-button"
                aria-label={pinned ? "Release passage" : "Pin passage"}
                aria-pressed={pinned}
                onClick={() => {
                  setPinned(!pinned);
                  void pageCommand(
                    tabId,
                    artifact,
                    pinned ? "TOMPATHY_RELEASE" : "TOMPATHY_FOCUS",
                    { region },
                  );
                }}
              >
                <Pin size={13} />
                <span>{pinned ? "Release" : "Pin"}</span>
              </button>
            </div>
          ) : (
            <span>Ready when you are.</span>
          )}
        </footer>
      </div>
      {modal && (
        <Modal
          title={
            {
              menu: "Your reading",
              context: "Build the context",
              source: "The source text",
              settings: "Your reader",
              import: "Connect an analysis",
              help: "A little closer to the maker",
              revision: "Review the new perspective",
              history: "Earlier accounts",
            }[modal]
          }
          onClose={() => {
            setModal(null);
            setError("");
          }}
        >
          {error && (
            <div className="message error" role="alert">
              {error}
            </div>
          )}
          {modal === "menu" && (
            <>
              <nav className="reader-menu" aria-label="Reader tools">
                <button onClick={() => setModal("source")}>
                  <BookOpen size={18} />
                  <span>
                    Source text
                    <small>
                      {artifact
                        ? `${artifact.regions.length} passages`
                        : "Capture or paste a text"}
                    </small>
                  </span>
                  <ChevronRight size={15} />
                </button>
                <button
                  onClick={() => {
                    setModal(null);
                    void capture();
                  }}
                >
                  <RefreshCw size={18} />
                  <span>Capture current page</span>
                  <ChevronRight size={15} />
                </button>
                <button onClick={() => setModal("context")}>
                  <Layers size={18} />
                  <span>
                    Context{context.length ? ` · ${context.length}` : ""}
                  </span>
                  <ChevronRight size={15} />
                </button>
                <button onClick={() => setModal("import")}>
                  <Upload size={18} />
                  <span>Import result</span>
                  <ChevronRight size={15} />
                </button>
                <button onClick={() => setModal("settings")}>
                  <Settings2 size={18} />
                  <span>Reader settings</span>
                  <ChevronRight size={15} />
                </button>
                {!!session.history?.length && (
                  <button onClick={() => setModal("history")}>
                    <BookOpen size={18} />
                    <span>
                      Earlier accounts
                      <small>{session.history.length} retained revisions</small>
                    </span>
                    <ChevronRight size={15} />
                  </button>
                )}
                <button onClick={() => setModal("help")}>
                  <CircleHelp size={18} />
                  <span>How ToMpathy works</span>
                  <ChevronRight size={15} />
                </button>
              </nav>
              {ready && (
                <label className="check-option">
                  <input
                    type="checkbox"
                    checked={view === "list"}
                    onChange={(e) =>
                      setView(e.target.checked ? "list" : "tree")
                    }
                  />{" "}
                  Show hypotheses as a list
                </label>
              )}
              {ready && (
                <label className="maker-picker">
                  Maker perspective
                  <select
                    value={activeMaker?.id}
                    onChange={(e) => {
                      setMaker(e.target.value);
                      setDetail(null);
                    }}
                  >
                    {packet!.makers.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.label} · {m.identity}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <p className="menu-status">
                {ready
                  ? `${isExample ? "Example" : "Analysis"} connected · revision ${packet!.revision}`
                  : "No analysis connected"}
              </p>
            </>
          )}
          {modal === "help" && (
            <>
              <p className="modal-lead">
                One text. More than one possible account.
              </p>
              <ol className="steps">
                <li>
                  <strong>Follow a passage.</strong> Hover to preview; click to
                  pin. Escape releases it. You can also select text or use the
                  passage list.
                </li>
                <li>
                  <strong>Explore the alternatives.</strong> Goals and process
                  respond to the passage. Select a hypothesis to inspect its
                  evidence.
                </li>
                <li>
                  <strong>Keep the maker in view.</strong> Values stay fixed
                  until you explicitly accept a new analysis revision.
                </li>
              </ol>
              <h3>Reading the page marks</h3>
              <p>
                Amber tint represents a named contribution estimate. A dotted
                underline independently marks high uncertainty. An outline marks
                your selection. No estimate means no tint.
              </p>
              <p>
                Word size expresses the provider’s declared support scale; it
                does not automatically mean probability. Example estimates are
                hand-authored.
              </p>
              <p>
                Process describes possible production events, not a recipe for
                reading or a map of expertise. More evidence can reveal
                alternatives or reduce confidence. Context collection never
                changes an account by itself.
              </p>
              <button className="primary-button" onClick={() => void example()}>
                Open the example <ArrowRight size={16} />
              </button>
            </>
          )}
          {modal === "source" && (
            <>
              <h3>{artifact?.title ?? "No source captured"}</h3>
              <label>
                Author to inspect
                <input
                  value={
                    session.authorLabel ??
                    (artifact?.authors?.length === 1
                      ? artifact.authors[0].label
                      : "")
                  }
                  maxLength={250}
                  placeholder="Author not identified"
                  onChange={(e) =>
                    setSession((s) => ({ ...s, authorLabel: e.target.value }))
                  }
                />
              </label>
              <p className="muted">
                {ready
                  ? `Analysis subject: ${activeMaker?.label}. Editing the requested author does not reassign existing claims.`
                  : "A page byline is a source attribution, not a verified identity. You can correct the requested author before exporting."}
              </p>
              {artifact?.capture && (
                <p className="muted">{artifact.capture.note}</p>
              )}
              <p className="muted">
                {artifact
                  ? `${artifact.regions.length} passages · ${artifact.truncated ? "Capture limited to 300,000 characters / 1,500 blocks" : "Text snapshot"} · ${tabId === null ? "Detached from a live page" : "Linked to the active page"}`
                  : "Browser pages without accessible text can be read from a pasted excerpt."}
              </p>
              {artifact && (
                <>
                  <p className="muted">
                    <SourceLink source={artifact.source} />
                  </p>
                  <div className="legend">
                    <span>▰ Contribution tint</span>
                    <span>┈ High uncertainty</span>
                    <span>□ Selection</span>
                  </div>
                  {estimate && (
                    <div className="contribution-explanation">
                      {contributionExplanation(packet!, region)
                        .split("\n")
                        .map((line) => (
                          <p key={line} className="muted">
                            {line}
                          </p>
                        ))}
                    </div>
                  )}
                  {ready &&
                    !!(
                      packet!.documentContribution?.evidence.length ||
                      estimate?.contribution?.evidence?.length
                    ) && (
                      <details>
                        <summary>Evidence for contribution</summary>
                        {[
                          ...new Set([
                            ...(packet!.documentContribution?.evidence ?? []),
                            ...(estimate?.contribution?.evidence ?? []),
                          ]),
                        ].map((id) => {
                          const e = packet!.evidence.find((e) => e.id === id)!;
                          return (
                            <blockquote key={id}>
                              <p>{e.excerpt}</p>
                              <cite>
                                <SourceLink source={e.source} />
                              </cite>
                              <small>{e.relationship}</small>
                            </blockquote>
                          );
                        })}
                      </details>
                    )}
                  <div className="passage-list">
                    {artifact.regions.map((r, i) => (
                      <button
                        key={r.id}
                        aria-pressed={r.id === region}
                        onClick={() => move(r.id, true)}
                      >
                        <small>{String(i + 1).padStart(2, "0")}</small>
                        <span>{r.anchor.exact}</span>
                      </button>
                    ))}
                  </div>
                  <button
                    className="secondary-button"
                    onClick={() => download("tompathy-capture.json", artifact)}
                  >
                    <Download size={15} /> Export capture for a provider
                  </button>
                  <button
                    className="secondary-button"
                    onClick={() =>
                      download(
                        "tompathy-analysis-request.json",
                        analysisHandoff(session),
                      )
                    }
                  >
                    <Download size={15} /> Export analysis request with selected
                    context
                  </button>
                </>
              )}
              {isExtension && (
                <button
                  className="secondary-button"
                  onClick={async () => {
                    cancelWork();
                    const request = serial.current;
                    try {
                      const selected = await captureSelection();
                      if (request !== serial.current) return;
                      await pageCommand(tabId, artifact, "TOMPATHY_CLEANUP");
                      setTabId(null);
                      setSession({ ...empty, artifact: selected });
                      setRegion("p1");
                      setStale(false);
                      setModal(null);
                      setNotice(
                        "Reading the selected excerpt as a detached snapshot.",
                      );
                    } catch (e) {
                      if (request === serial.current)
                        setError((e as Error).message);
                    }
                  }}
                >
                  <MousePointer2 size={15} /> Use selected page text
                </button>
              )}
              <label>
                Paste a different text
                <textarea
                  value={paste}
                  maxLength={300000}
                  onChange={(e) => setPaste(e.target.value)}
                  placeholder="Paste text, with a blank line between passages…"
                />
              </label>
              <button
                className="primary-button"
                disabled={!paste.trim()}
                onClick={async () => {
                  cancelWork();
                  const request = serial.current;
                  const a = await makeArtifact(
                    paste.split(/\n\s*\n/),
                    "tompathy:pasted",
                    "Pasted text",
                  );
                  if (request !== serial.current) return;
                  await pageCommand(tabId, artifact, "TOMPATHY_CLEANUP");
                  setTabId(null);
                  setSession({ ...empty, artifact: a });
                  setRegion("p1");
                  setStale(false);
                  setModal(null);
                }}
              >
                Use pasted text <ArrowRight size={15} />
              </button>
            </>
          )}
          {modal === "import" && (
            <>
              <p className="modal-lead">
                Bring the hypotheses. Keep their evidence.
              </p>
              <p>
                Import a ToMpathy result packet that matches this text snapshot
                and scope. Sounding Line’s live connection is awaiting an
                adapter.
              </p>
              <label className="upload-zone">
                <Upload size={23} />
                <strong>Choose a result packet</strong>
                <span>Version 1.0 / 1.1 JSON · up to 2 MB</span>
                <input
                  type="file"
                  accept=".json,application/json"
                  onChange={(e) => void readFile(e.target.files?.[0], "packet")}
                />
              </label>
              <details>
                <summary>Or paste JSON</summary>
                <textarea
                  aria-label="Result JSON"
                  value={importText}
                  onChange={(e) => setImportText(e.target.value)}
                  placeholder={'{"schemaVersion": "1.0", …}'}
                />
                <button
                  className="primary-button"
                  disabled={!importText.trim()}
                  onClick={() => void loadPacket(importText)}
                >
                  Validate & import
                </button>
              </details>
              <button
                className="text-button"
                onClick={async () =>
                  download(
                    "tompathy-example-packet.json",
                    await createExample(artifact?.source ?? "tompathy:example"),
                  )
                }
              >
                Download example format <Download size={14} />
              </button>
              <p className="muted">
                The example format only matches the bundled example text.
              </p>
            </>
          )}
          {modal === "context" && (
            <>
              <label className="scope-picker">
                Analysis scope
                <select
                  aria-label="Analysis scope"
                  value={scope}
                  onChange={(e) => {
                    setSession((s) => ({
                      ...s,
                      scope: e.target.value as Scope,
                    }));
                    setDetail(null);
                  }}
                >
                  <option value="artifact">This artifact</option>
                  <option value="context">Artifact + selected context</option>
                </select>
              </label>

              <p className="modal-lead">More to consider. Collected by you.</p>
              <p>
                Add an excerpt or retrieve up to three public pages. Select the
                items you want an analysis to consider. Collection alone does
                not change the estimates.
              </p>
              <p className="muted">
                These sources are available to you. Their presence does not
                establish what the author knew or believed.
              </p>
              {context.map((c) => (
                <div className="context-item" key={c.id}>
                  <header>
                    <label>
                      <input
                        type="checkbox"
                        checked={c.selected}
                        onChange={(e) =>
                          setSession((s) => ({
                            ...s,
                            context: s.context.map((x) =>
                              x.id === c.id
                                ? { ...x, selected: e.target.checked }
                                : x,
                            ),
                          }))
                        }
                      />
                      <span>{sourceLabel(c.source)}</span>
                    </label>
                    <IconButton
                      label={`Remove ${sourceLabel(c.source)}`}
                      onClick={() =>
                        setSession((s) => ({
                          ...s,
                          context: s.context.filter((x) => x.id !== c.id),
                        }))
                      }
                    >
                      <Trash2 size={15} />
                    </IconButton>
                  </header>
                  <p>{c.excerpt}</p>
                  <small>
                    {c.lineage} · {new Date(c.retrievedAt).toLocaleString()} ·{" "}
                    <SourceLink source={c.source} />
                  </small>
                </div>
              ))}
              <label>
                Source or title
                <input
                  value={contextSource}
                  onChange={(e) => setContextSource(e.target.value)}
                />
              </label>
              <label>
                Excerpt
                <textarea
                  value={contextPaste}
                  maxLength={20000}
                  onChange={(e) => setContextPaste(e.target.value)}
                  placeholder="Something that adds perspective…"
                />
              </label>
              <div className="button-row">
                <button
                  className="secondary-button"
                  onClick={() => addContext(contextPaste, contextSource)}
                >
                  <Plus size={15} /> Add excerpt
                </button>
                <label className="file-button">
                  <Upload size={15} /> Attach .txt / .md
                  <input
                    type="file"
                    accept=".txt,.md,text/plain,text/markdown"
                    onChange={(e) =>
                      void readFile(e.target.files?.[0], "context")
                    }
                  />
                </label>
              </div>
              <details>
                <summary>Retrieve public sources</summary>
                <p className="muted">
                  HTTPS only · 256 KB per page · 30 seconds total · no recursive
                  crawl. Redirects are declined. The browser asks for access to
                  each selected origin.
                </p>
                <label>
                  URLs, one per line
                  <textarea
                    value={urls}
                    onChange={(e) => setUrls(e.target.value)}
                    placeholder="https://example.com/about"
                  />
                </label>
                {collecting ? (
                  <button
                    className="secondary-button"
                    onClick={() => collector.current?.abort()}
                  >
                    <LoaderCircle className="spin" size={15} /> Cancel
                    collection
                  </button>
                ) : (
                  <button
                    className="primary-button"
                    onClick={() => void collect()}
                  >
                    <Link size={15} /> Collect selected sources
                  </button>
                )}
                <div role="status">
                  {collectionStatus.map((s, i) => (
                    <p className="muted" key={i}>
                      {s}
                    </p>
                  ))}
                </div>
              </details>
              {isExample && (
                <div className="example-revision">
                  <span className="eyebrow">TRY A CHANGE OF MIND</span>
                  <h3>What if the choices came from the brief?</h3>
                  <p>
                    A fictional notebook changes the process account. Preview it
                    before updating the maker snapshot.
                  </p>
                  <button
                    className="secondary-button"
                    onClick={() => void revision()}
                  >
                    Preview example revision <ArrowRight size={15} />
                  </button>
                </div>
              )}
            </>
          )}
          {modal === "revision" && pending && (
            <>
              <span className="badge">
                {pending.origin} · revision {pending.revision}
              </span>
              <p className="modal-lead">New evidence, an explicit change.</p>
              <p>
                {pending.changeExplanation ??
                  "The imported packet offers a new analysis of this artifact. Accepting it replaces the current goals, process, and maker-level values."}
              </p>
              <div className="revision-compare">
                <div>
                  <small>CURRENT VALUES</small>
                  {packet?.hypotheses
                    .filter((h) => h.kind === "value")
                    .map((h) => (
                      <p key={h.id}>{h.label}</p>
                    ))}
                </div>
                <ArrowRight size={18} />
                <div>
                  <small>PROPOSED VALUES</small>
                  {pending.hypotheses
                    .filter((h) => h.kind === "value")
                    .map((h) => (
                      <p key={h.id}>{h.label}</p>
                    ))}
                </div>
              </div>
              <button
                className="primary-button"
                onClick={() => {
                  const nextContext =
                    pending.origin === "synthetic example"
                      ? [exampleContext]
                      : context;
                  const reason = artifact
                    ? matchPacket(
                        pending,
                        artifact,
                        pending.scope.kind,
                        nextContext,
                      )
                    : "Capture a source first.";
                  if (reason || stale) {
                    setError(
                      reason ||
                        "Recapture the changed source before accepting a revision.",
                    );
                    return;
                  }
                  setSession((s) => acceptRevision(s, pending, nextContext));
                  setPending(null);
                  setDetail(null);
                  setModal(null);
                  setNotice(
                    "Analysis revision accepted. The new maker snapshot stays fixed across passages.",
                  );
                }}
              >
                <Check size={16} /> Accept this revision
              </button>
              <button
                className="secondary-button"
                onClick={() => {
                  setPending(null);
                  setModal(null);
                }}
              >
                Keep current analysis
              </button>
            </>
          )}
          {modal === "history" && (
            <>
              <p className="muted">
                Previous accounts stay inspectable. Viewing one does not replace
                the accepted account or change page marks. Up to five are
                retained in this session.
              </p>
              {[...(session.history ?? [])].reverse().map((entry, i) => (
                <details key={`${entry.packet.id}-${i}`}>
                  <summary>
                    Revision {entry.packet.revision} ·{" "}
                    {entry.packet.provider.id}
                  </summary>
                  <p>
                    {entry.packet.changeExplanation ??
                      "Earlier account before new evidence was accepted."}
                  </p>
                  <p className="muted">
                    {entry.packet.origin} · {entry.packet.scope.kind} ·{" "}
                    {entry.context.filter((c) => c.selected).length} selected
                    sources
                  </p>
                  {entry.packet.hypotheses.map((h) => (
                    <details key={h.id}>
                      <summary>{h.label}</summary>
                      <p>{h.description}</p>
                      <p className="muted">
                        {h.status} · {interpretationLabel(h)}
                      </p>
                      {h.evidence.map((id) => {
                        const e = entry.packet.evidence.find(
                          (e) => e.id === id,
                        )!;
                        return (
                          <blockquote key={id}>
                            <p>{e.excerpt}</p>
                            <cite>{e.source}</cite>
                            <small>{e.relationship}</small>
                          </blockquote>
                        );
                      })}
                    </details>
                  ))}
                  <button
                    className="secondary-button"
                    onClick={() =>
                      download(
                        `tompathy-revision-${entry.packet.revision}.json`,
                        entry.packet,
                      )
                    }
                  >
                    <Download size={15} /> Export this account
                  </button>
                </details>
              ))}
            </>
          )}
          {modal === "settings" && (
            <>
              <h3>Appearance</h3>
              <div className="theme-options">
                {["system", "light", "dark"].map((t) => (
                  <button
                    key={t}
                    aria-pressed={theme === t}
                    onClick={() => {
                      setTheme(t);
                      void writeTheme(t);
                    }}
                  >
                    <Sun size={17} />
                    {t}
                  </button>
                ))}
              </div>
              <h3>This reading session</h3>
              <p>
                Preferences persist. Captured text and context stay in this
                browser session unless you export them.
              </p>
              <p className="scope-summary">
                Saved scope:{" "}
                <strong>
                  {scope === "artifact"
                    ? "This artifact"
                    : "Artifact + selected context"}
                </strong>
              </p>
              <div className="button-row">
                <button
                  className="secondary-button"
                  onClick={() => download("tompathy-session.json", session)}
                >
                  <Download size={15} /> Save session
                </button>
                <label className="file-button">
                  <Upload size={15} /> Load session
                  <input
                    type="file"
                    accept=".json"
                    onChange={(e) =>
                      void readFile(e.target.files?.[0], "session")
                    }
                  />
                </label>
              </div>
              <button
                className="danger-button"
                onClick={async () => {
                  cancelWork();
                  await pageCommand(tabId, artifact, "TOMPATHY_CLEANUP");
                  setSession(empty);
                  setTabId(null);
                  setDetail(null);
                  setPending(null);
                  setStale(false);
                  setNotice("Session cleared.");
                  setModal(null);
                }}
              >
                <Trash2 size={15} /> Clear session
              </button>
              <h3>Current analysis</h3>
              <p>
                {packet
                  ? `${packet.provider.id} · ${packet.provider.method} · revision ${packet.revision}. Origin: ${packet.origin}.`
                  : "No inference provider is connected."}
              </p>
              <h3>Reading beside a page</h3>
              <p>
                Click ToMpathy in the Chrome toolbar, or press Alt+Shift+Y.
                Chrome controls which side the panel opens on. You can choose
                the right side in Chrome’s Appearance settings.
              </p>
            </>
          )}
        </Modal>
      )}
    </div>
  );
}

function ProcessTree({
  nodes,
  edges,
  focus,
  local,
  onInspect,
}: {
  nodes: Hypothesis[];
  edges: Packet["process"]["edges"];
  focus?: string;
  local: string[];
  onInspect: (h: Hypothesis) => void;
}) {
  const byId = new Map(nodes.map((h) => [h.id, h]));
  const allLinks = edges.filter((e) => byId.has(e.from) && byId.has(e.to));
  const links = allLinks.filter(
    (e) => e.kind === "precedes" || e.kind === "enables",
  );
  const visited = new Set<string>();
  const branch = (h: Hypothesis, relationship?: string): ReactNode => {
    if (visited.has(h.id))
      return (
        <li key={`reference-${h.id}`}>
          <button className="tree-node is-distant" onClick={() => onInspect(h)}>
            <span aria-hidden="true">↗</span>
            <span>
              {h.label}
              <small className="value-kind">
                Shared event · {relationship}
              </small>
            </span>
          </button>
        </li>
      );
    visited.add(h.id);
    const children = links.filter((e) => e.from === h.id);
    return (
      <li key={h.id}>
        <button
          className={`tree-node ${focus === h.id ? "is-focus" : ""} ${local.includes(h.id) ? "" : "is-distant"} ${h.status === "unknown" ? "is-unknown" : ""}`}
          title={relationship ? `${relationship}: ${h.label}` : h.description}
          onClick={() => onInspect(h)}
        >
          <span className="node-dot" aria-hidden="true">
            {h.status === "unknown" ? "?" : ""}
          </span>
          <span>
            {h.label}
            {relationship && (
              <small className="value-kind">{relationship}</small>
            )}
          </span>
          {focus === h.id && (
            <span className="focus-mark" aria-label="in focus" />
          )}
          {relationship && <span className="sr-only"> · {relationship}</span>}
        </button>
        {allLinks
          .filter((e) => e.from === h.id && !links.includes(e))
          .map((e, i) => (
            <p className="cross-link" key={i}>
              {e.relationship} · {byId.get(e.to)!.label}
            </p>
          ))}
        {children.length > 0 && (
          <ul>
            {children.map((e) => branch(byId.get(e.to)!, e.relationship))}
          </ul>
        )}
      </li>
    );
  };
  const roots = nodes.filter((h) => !links.some((e) => e.to === h.id));
  const forest = roots.map((h) => branch(h));
  // Cyclic or disconnected provider graphs still expose each hypothesis once.
  const remaining = nodes
    .filter((h) => !visited.has(h.id))
    .map((h) => branch(h));
  return (
    <ul className="process-tree" aria-label="Possible process relationships">
      {forest}
      {remaining}
    </ul>
  );
}

function supportWeight(h: Hypothesis) {
  return h.support
    ? (h.support.value - h.support.scale[0]) /
        (h.support.scale[1] - h.support.scale[0])
    : -1;
}
function SourceLink({ source }: { source: string }) {
  return /^https?:\/\//i.test(source) ? (
    <a href={source} target="_blank" rel="noreferrer noopener" title={source}>
      {sourceLabel(source)} ↗
    </a>
  ) : (
    <span>{sourceLabel(source)}</span>
  );
}
function sourceLabel(source: string) {
  try {
    return new URL(source).hostname || source;
  } catch {
    return source;
  }
}
export function ExampleArticle({
  active = "",
  pinned = false,
  related = [],
  onMove = () => {},
}: {
  active?: string;
  pinned?: boolean;
  related?: string[];
  onMove?: (id: string, pin?: boolean) => void;
}) {
  const standalone = isExtension && location.pathname.endsWith("example.html");
  return (
    <div className="example-page">
      <nav>
        <span className="journal-mark">
          FIELDNOTES<span>ON EVERYDAY DESIGN</span>
        </span>
        <span className="journal-issue">
          No. 014 <span>—</span> Places & people
        </span>
      </nav>
      <div className="example-ribbon">
        <span>
          <span className="tiny-dot" /> A fictional artifact, made for exploring
          ToMpathy
        </span>
        {standalone ? (
          <button
            onClick={async () => {
              const tab = await chrome.tabs.getCurrent();
              if (tab?.id) await chrome.sidePanel.open({ tabId: tab.id });
            }}
          >
            Open Maker Reader <ArrowRight size={14} />
          </button>
        ) : (
          <span>
            Hover a passage to begin <MousePointer2 size={13} />
          </span>
        )}
      </div>
      <article>
        <div className="article-kicker" data-tompathy-ui>
          SMALL INTERVENTIONS / 06 MIN READ
        </div>
        <h1
          data-passage="p1"
          onMouseEnter={() => onMove("p1")}
          onClick={() => onMove("p1", true)}
        >
          {exampleText[0]}
        </h1>
        <div className="article-deck" data-tompathy-ui>
          On making room for the things
          <br />
          we cannot quite plan.
        </div>
        <div className="article-byline" data-tompathy-ui>
          <span className="author-avatar">F</span>
          <span>
            The garden designer{" "}
            <small>September 19, 2026 · Fictional author</small>
          </span>
          <span className="article-rule" />
        </div>
        {exampleText.slice(1).map((text, i) => (
          <p
            key={i}
            data-passage={`p${i + 2}`}
            tabIndex={0}
            className={`${active === `p${i + 2}` ? "active-passage" : ""} ${related.includes(`p${i + 2}`) ? "related-passage" : ""}`}
            onMouseEnter={() => onMove(`p${i + 2}`)}
            onClick={() => onMove(`p${i + 2}`, true)}
            onFocus={() => onMove(`p${i + 2}`)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") onMove(`p${i + 2}`, true);
            }}
          >
            <span className="passage-number" aria-hidden="true">
              {String(i + 1).padStart(2, "0")}
              {pinned && active === `p${i + 2}` ? " ·" : ""}
            </span>
            {text}
          </p>
        ))}
        <div className="article-end" data-tompathy-ui>
          <span>✳</span>
          <span>A place to begin.</span>
        </div>
      </article>
      <footer>
        FIELDNOTES{" "}
        <span>An example text. No real person is being analyzed.</span>
      </footer>
    </div>
  );
}
