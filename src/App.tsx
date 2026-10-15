import { demoGlobalValues, demoWorkValues } from "./core/example-values";
import { ProviderOptions, readProvider } from "./components/ProviderOptions";
import { PopulationValues } from "./components/PopulationValues";
import { RecordedProcess } from "./components/RecordedProcess";
import { makeProvider, type ProviderSettings } from "./core/provider";
import { findSentence } from "./find-sentence";
import { selectionTransition } from "./selection-transition";
import { ReadingText, textOffset } from "./components/ReadingText";
import { ghostAt } from "./core/ghost";
import { readingFile, parseReadingFile } from "./core/reading-file";
import { ReadingPreview } from "./components/ReadingPreview";
import { createArtExample, artContext } from "./core/art-example";
import { createWebsiteDemo } from "./core/website-demo";
import { isWebsiteDemo } from "./core/site-demo-scope";
import { ContextTimeline } from "./components/ContextTimeline";
import {
  bylineContext,
  collectCreatorContext,
  clearContextCache,
  type ContextReport,
} from "./core/creator-context";
import {
  ContextProgress,
  type ContextWork,
} from "./components/ContextProgress";
import { attentionAt, attentionForNode } from "./core/attention";
import { ValueTabs, type ValuesTab } from "./components/ValueTabs";
import { SelectionLock } from "./components/SelectionLock";
import { blockedFocusTracker } from "./core/lock";
import { GoalCloud } from "./components/GoalCloud";
import { ProcessHierarchy } from "./components/ProcessHierarchy";
import { ValueList, ValueDetails } from "./components/ValueList";
import { SectionTitle, explanations } from "./components/HoverCard";
import { sentences, regionSentences } from "./core/sentences";
import type { GoalNode } from "./core/hierarchy";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
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
import {
  createExample,
  exampleContext,
  exampleText,
  exampleEmphasis,
} from "./core/example";
import { collectSources, publicURL, contextSourceURL } from "./core/collector";
import { githubRepository } from "./core/public-source";
import {
  acceptRevision,
  analysisHandoff,
  contributionExplanation,
  interpretationLabel,
} from "./core/reading";
import { contextIdentity, mergeContext } from "./core/context";
import {
  capturePage,
  PageCaptureUnavailable,
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
      <img className="brand-symbol" src="./icon32.png" alt="" />
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
      className={`modal ${title === "Options" ? "options-modal" : ""}`}
      aria-label={title}
      onKeyDown={(e) => {
        if (e.key === "Escape") e.stopPropagation();
      }}
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
  const [provider, setProvider] = useState<ProviderSettings>({ kind: "none" });
  const [analyzing, setAnalyzing] = useState(false);
  const analyzer = useRef<AbortController | null>(null);
  useEffect(() => {
    let live = true;
    void readProvider().then((p) => {
      if (live) setProvider(p);
    });
    return () => {
      live = false;
      analyzer.current?.abort();
    };
  }, []);
  const [session, setSession] = useState<Session>(empty),
    [hydrated, setHydrated] = useState(false),
    [tabId, setTabId] = useState<number | null>(null),
    [region, setRegion] = useState("p2"),
    [pinned, setPinned] = useState(false),
    [foundInPage, setFoundInPage] = useState(false),
    [navigationRequest, setNavigationRequest] = useState(0),
    [lockReminder, setLockReminder] = useState(0),
    [valuesTab, setValuesTab] = useState<ValuesTab>("work"),
    [sentenceOffset, setSentenceOffset] = useState(0),
    [sourceHover, setSourceHover] = useState(false),
    [relatedNode, setRelatedNode] = useState<GoalNode | null>(null),
    [lockedNode, setLockedNode] = useState<GoalNode | null>(null),
    [busy, setBusy] = useState(false),
    [stale, setStale] = useState(false),
    [notice, setNotice] = useState(""),
    [error, setError] = useState(""),
    [contextEnabled, setContextEnabled] = useState(
      () => localStorage.getItem("tompathy-context-enabled") === "true",
    ),
    [followLinks, setFollowLinks] = useState(
      () => localStorage.getItem("tompathy-follow-links") === "true",
    ),
    [contextReport, setContextReport] = useState<ContextReport | null>(null),
    [useGitHub, setUseGitHub] = useState(
      () => localStorage.getItem("tompathy-use-github") !== "false",
    ),
    [contextWork, setContextWork] = useState<ContextWork | null>(null),
    [tour, setTour] = useState<number | null>(null),
    [maker, setMaker] = useState(""),
    [detail, setDetail] = useState<Hypothesis | null>(null),
    [modal, setModal] = useState<
      | "qa"
      | "menu"
      | "context"
      | "creator-context"
      | "source"
      | "settings"
      | "import"
      | "help"
      | "revision"
      | "history"
      | "claims"
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
    current = useRef({ session, tabId, pinned }),
    blockedFocus = useRef(blockedFocusTracker());
  const helpSection = useRef<keyof typeof explanations | null>(null);
  const openSectionHelp = (kind: keyof typeof explanations) => {
    helpSection.current = kind;
    setModal("help");
  };
  useEffect(() => {
    if (modal !== "help" || !helpSection.current) return;
    const heading = document.getElementById(`help-${helpSection.current}`);
    if (heading) {
      const header = heading.closest("dialog")?.querySelector("header");
      heading.style.scrollMarginTop = `${(header?.offsetHeight ?? 64) + 12}px`;
      heading.scrollIntoView({ block: "start" });
    }
    helpSection.current = null;
  }, [modal]);
  current.current = { session, tabId, pinned };
  const sentenceTransition = useRef(selectionTransition());
  useEffect(() => {
    const node = document.querySelector<HTMLElement>(
      ".example-page .active-sentence",
    );
    if (!node) return sentenceTransition.current.clear();
    const range = document.createRange();
    range.selectNodeContents(node);
    const key = `${node.closest("[data-passage]")?.getAttribute("data-passage")}:${node.dataset.sentence}`;
    sentenceTransition.current.show(range, key);
  }, [region, sentenceOffset, relatedNode, pinned, sourceHover]);
  useEffect(() => {
    const clear = () => sentenceTransition.current.clear();
    window.addEventListener("scroll", clear, true);
    return () => {
      window.removeEventListener("scroll", clear, true);
      clear();
    };
  }, []);
  useEffect(() => {
    blockedFocus.current.reset();
    setLockReminder(0);
  }, [pinned, lockedNode?.id, region, sentenceOffset]);
  const blocked = (key: string, weight = 1) => {
    if (
      pinned &&
      blockedFocus.current.attempt(key, performance.now(), weight)
    ) {
      setLockReminder((n) => n + 1);
      void pageCommand(tabId, session.artifact, "TOMPATHY_LOCK_REMINDER");
    }
  };
  useEffect(() => {
    if (contextWork?.phase === "done" || contextWork?.phase === "error") {
      const timer = setTimeout(() => setContextWork(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [contextWork]);
  const { artifact, packet, scope, context } = session;
  // Invalidate in-flight requests when their evidence changes, including a
  // same-ID context edit. A late response must never replace a newer reading.
  const analysisKey = JSON.stringify([
    artifact,
    scope,
    context.filter((c) => c.selected),
    provider,
    stale,
  ]);
  const analysisCurrent = useRef(analysisKey);
  analysisCurrent.current = analysisKey;
  useEffect(() => {
    analyzer.current?.abort();
    setAnalyzing(false);
  }, [analysisKey]);
  async function analyze(history?: "wikipedia") {
    if (!artifact || stale || provider.kind === "none") return;
    analyzer.current?.abort();
    const job = new AbortController();
    analyzer.current = job;
    const key = analysisKey;
    setAnalyzing(true);
    setError("");
    setNotice("");
    try {
      const result = await makeProvider(provider)!.analyze({
        requestId: crypto.randomUUID(),
        artifact,
        scope,
        context,
        signal: job.signal,
        ...(history ? { history } : {}),
      });
      if (job.signal.aborted || analysisCurrent.current !== key) return;
      if (current.current.session.packet) {
        setPending(result);
        setModal("revision");
      } else {
        setSession((s) => ({ ...s, packet: result }));
        setMaker(result.makers[0].id);
      }
      setNotice(
        "Analysis received. Estimates depend on the source's available evidence and admissions.",
      );
    } catch (e) {
      if (!job.signal.aborted && analysisCurrent.current === key)
        setError((e as Error).message);
    } finally {
      if (analyzer.current === job) setAnalyzing(false);
    }
  }
  const mismatch =
    packet && artifact ? matchPacket(packet, artifact, scope, context) : null;
  const ready = !!packet && !mismatch && !stale;
  useEffect(() => {
    if (ready && !localStorage.getItem("tompathy-guide-offered-040")) {
      localStorage.setItem("tompathy-guide-offered-040", "yes");
      setTour(-1);
    }
  }, [ready]);
  useEffect(() => {
    // Dismiss the invitation after selection, but never move controls under a
    // pointer using the panel (notably the first wheel gesture on a reel).
    // A deliberately started tour remains until the reader dismisses it.
    if (pinned && tour === -1 && !document.querySelector(".reader:hover"))
      setTour(null);
  }, [pinned, tour]);
  const activeMaker =
    packet?.makers.find((m) => m.id === maker) ?? packet?.makers[0];
  const hierarchyNodes = useMemo(
    () =>
      ready
        ? (packet?.goalHierarchy?.nodes ?? []).filter(
            (n) => n.maker === activeMaker?.id,
          )
        : [],
    [ready, packet, activeMaker?.id],
  );
  const creatorName =
    (ready && activeMaker?.identity !== "unknown"
      ? activeMaker?.label
      : null) ||
    session.authorLabel ||
    (artifact?.authors?.length === 1 ? artifact.authors[0].label : null) ||
    (artifact?.authors?.length
      ? "Multiple creators listed"
      : "Creator not identified");
  const hypotheses = ready
    ? packet!.hypotheses.filter((h) => h.makers.includes(activeMaker!.id))
    : [];
  const attentionTarget = pinned
    ? lockedNode
      ? lockedNode.span
      : { region, start: sentenceOffset }
    : relatedNode
      ? relatedNode.span
      : sourceHover
        ? { region, start: sentenceOffset }
        : null;
  const attentionNode = pinned ? lockedNode : relatedNode;
  const goals =
    ready && attentionNode
      ? attentionForNode(packet!, activeMaker!.id, attentionNode)
      : ready && attentionTarget
        ? attentionAt(
            packet,
            activeMaker!.id,
            attentionTarget.region,
            attentionTarget.start,
          )
        : [];
  const values = hypotheses.filter(
    (h) => h.kind === "value" && h.status !== "unknown",
  );
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
    analyzer.current?.abort();
    setAnalyzing(false);
    setContextReport(null);
    serial.current++;
    collector.current?.abort();
    setCollecting(false);
    setBusy(false);
    setPending(null);
    setContextWork(null);
  }
  async function capture() {
    cancelWork();
    const request = serial.current;
    setBusy(true);
    setError("");
    setNotice("");
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
      setLockedNode(null);
      setRelatedNode(null);
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
      // The live DOM is the source of truth. The commissioned website gets a
      // fresh demo packet for exactly the text currently visible in this capture.
      if (
        isWebsiteDemo(result.artifact.source) &&
        !result.restored &&
        (!resultPacket ||
          ["tompathy-art-demo", "tompathy-website-demo"].includes(
            resultPacket.provider.id,
          ))
      )
        resultPacket = createWebsiteDemo(result.artifact);
      if (
        !resultPacket &&
        result.artifact.source.split("?")[0] ===
          chrome.runtime.getURL("example.html")
      ) {
        const candidate = await createExample(result.artifact.source);
        if (!matchPacket(candidate, result.artifact, "artifact", []))
          resultPacket = candidate;
      }
      if (
        !resultPacket &&
        result.artifact.source.split("?")[0] ===
          chrome.runtime.getURL("art.html")
      ) {
        const candidate = await createArtExample(result.artifact.source);
        if (!matchPacket(candidate, result.artifact, "artifact", []))
          resultPacket = candidate;
      }
      if (request !== serial.current) return;
      setSession(
        result.restored ?? {
          sessionVersion: "1.0",
          artifact: result.artifact,
          contextSources: result.contextSources,
          repositoryLinks: result.repositoryLinks,
          packet: resultPacket,
          scope: resultPacket?.scope.kind ?? "artifact",
          context:
            resultPacket?.scope.kind === "context"
              ? previous.context
              : resultPacket?.provider.id === "tompathy-art-demo"
                ? [{ ...artContext, selected: false }]
                : resultPacket?.origin === "synthetic example"
                  ? [{ ...exampleContext, selected: false }]
                  : [],
          history: resultPacket ? previous.history : [],
          authorLabel:
            previous.artifact?.id === result.artifact.id
              ? previous.authorLabel
              : undefined,
        },
      );
    } catch (e) {
      if (request !== serial.current) return;
      setTabId(null);
      setSession(empty);
      if (e instanceof PageCaptureUnavailable) setNotice(e.message);
      else setError((e as Error).message);
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
    setLockedNode(null);
    setRelatedNode(null);
    setRegion("p2");
    const fieldnotes =
      new URLSearchParams(location.search).get("demo") === "fieldnotes";
    const create = fieldnotes ? createExample : createArtExample;
    const context = fieldnotes ? exampleContext : artContext;
    const file = fieldnotes ? "example.html" : "art.html";
    if (isExtension) {
      if (!fieldnotes) {
        await chrome.tabs.create({ url: "https://abrahamhaskins.org/art/" });
        setNotice(
          "On the website, click the ToMpathy toolbar icon to open its reader.",
        );
        return;
      }
      const tab = await chrome.tabs.create({
        url: chrome.runtime.getURL(file),
      });
      setTabId(tab.id ?? null);
      const p = await create(chrome.runtime.getURL(file));
      setSession({
        ...empty,
        artifact: p.artifact,
        packet: p,
        context: [{ ...context, selected: false }],
      });
      setNotice("Move across the example text to explore.");
    } else {
      const p = await create();
      setSession({
        ...empty,
        artifact: p.artifact,
        packet: p,
        context: [{ ...context, selected: false }],
      });
    }
  }
  useEffect(() => {
    let alive = true;
    (async () => {
      const saved = SessionSchema.safeParse(await readSession());
      if (alive && saved.success) {
        if (
          !isExtension &&
          new URLSearchParams(location.search).get("demo") !== "fieldnotes" &&
          saved.data.artifact?.source === "tompathy:example"
        ) {
          const p = await createArtExample();
          if (alive)
            setSession({
              ...empty,
              artifact: p.artifact,
              packet: p,
              context: [artContext],
            });
        } else if (
          saved.data.artifact?.source === "tompathy:example" &&
          saved.data.packet?.origin === "synthetic example" &&
          (saved.data.artifact.title !== exampleText[0] ||
            !saved.data.packet.goalHierarchy?.nodes.some(
              (n) => n.id === "editing",
            ))
        ) {
          const p = await createExample();
          if (alive)
            setSession({
              ...empty,
              artifact: p.artifact,
              packet: p,
              context: [{ ...exampleContext, selected: false }],
            });
        } else setSession(saved.data);
      }
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
        void chrome.tabs
          .query({ active: true, currentWindow: true })
          .then(([tab]) => {
            if (tab?.id === m.tabId) void capture();
          });
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
      if (m.type === "TOMPATHY_SCROLLED") setFoundInPage(false);
      if (m.type === "TOMPATHY_FOUND") setFoundInPage(true);
      if (m.type === "TOMPATHY_SELECT") {
        setRegion(m.region);
        setSentenceOffset(m.offset ?? 0);
        setSourceHover(true);
        setRelatedNode(null);
        setPinned(m.pinned);
        setLockedNode(null);
        setDetail(null);
      }
      if (m.type === "TOMPATHY_UNLOCK") {
        setPinned(false);
        setLockedNode(null);
        setRelatedNode(null);
        setSourceHover(false);
      }
      if (m.type === "TOMPATHY_LOCK_REMINDER" && c.pinned) {
        blockedFocus.current.acknowledge(performance.now());
        setLockReminder((n) => n + 1);
      }
      // Pointer gaps retain the last inspected frame; the next SELECT replaces it.
      if (m.type === "TOMPATHY_STALE") {
        cancelWork();
        setStale(true);
        setDetail(null);
        if (c.session.artifact && isWebsiteDemo(c.session.artifact.source))
          void capture();
      }
    };
    const changed = async (info: chrome.tabs.OnActivatedInfo) => {
      // Activation in another Chrome window must not disturb this reader.
      const [active] = await chrome.tabs.query({
        active: true,
        currentWindow: true,
      });
      if (active?.id !== info.tabId) return;
      cancelWork();
      void pageCommand(
        current.current.tabId,
        current.current.session.artifact,
        "TOMPATHY_CLEANUP",
      );
      setSession(empty);
      setDetail(null);
      setPinned(false);
      setLockedNode(null);
      setRelatedNode(null);
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
    setPinned(false);
    setLockedNode(null);
    setRelatedNode(null);
    void pageCommand(tabId, artifact, "TOMPATHY_RELEASE");
  }, [packet?.id, packet?.revision, activeMaker?.id, ready]);
  useEffect(() => {
    void markPage(tabId, artifact, ready ? packet : null, activeMaker?.id);
  }, [tabId, artifact, packet, ready, activeMaker?.id]);
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (
        e.key === "Escape" &&
        !e.defaultPrevented &&
        !document.querySelector("dialog[open]")
      ) {
        if (tour !== null) {
          setTour(null);
          return;
        }
        setPinned(false);
        setLockedNode(null);
        setRelatedNode(null);
        setSourceHover(false);
        if (document.activeElement?.closest(".example-page"))
          (document.activeElement as HTMLElement).blur();
        void pageCommand(tabId, artifact, "TOMPATHY_RELEASE");
      }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [tabId, artifact, tour]);
  const unlock = () => {
    setPinned(false);
    setLockedNode(null);
    setRelatedNode(null);
    setSourceHover(false);
    if (document.activeElement?.closest(".example-page"))
      (document.activeElement as HTMLElement).blur();
    void pageCommand(tabId, artifact, "TOMPATHY_RELEASE");
  };
  useEffect(() => {
    const release = () => unlock();
    window.addEventListener("dblclick", release);
    return () => window.removeEventListener("dblclick", release);
  }, [tabId, artifact]);
  const cancelFind = useRef<() => void>(() => {});
  const autoFind = useRef(false);
  const finding = useRef(false);
  useEffect(() => {
    setFoundInPage(false);
    cancelFind.current();
    finding.current = false;
  }, [pinned, lockedNode?.id, region, sentenceOffset, tabId]);
  useEffect(() => {
    if (!preview) return;
    const scroll = (e: Event) => {
      if (
        e.target === document ||
        (e.target as Element).closest?.(".example-page")
      )
        if (!finding.current) setFoundInPage(false);
    };
    document.addEventListener("scroll", scroll, true);
    return () => {
      document.removeEventListener("scroll", scroll, true);
      cancelFind.current();
    };
  }, [preview]);
  const findLocked = () => {
    if (!pinned || !artifact) return;
    setFoundInPage(true);
    const id = lockedNode?.span?.region ?? region,
      start = lockedNode?.span?.start ?? sentenceOffset;
    if (isExtension) {
      void pageCommand(tabId, artifact, "TOMPATHY_FIND", {
        region: id,
        offset: start,
      });
      return;
    }
    const elements =
      lockedNode && !lockedNode.span
        ? lockedNode.regions.flatMap((region) => [
            ...document.querySelectorAll(
              `[data-passage="${CSS.escape(region)}"] [data-sentence]`,
            ),
          ])
        : (() => {
            const passage = artifact.regions.find((r) => r.id === id);
            const index = (passage ? regionSentences(passage) : []).findIndex(
              (s) => s.start <= start && start < s.end,
            );
            return [
              ...document.querySelectorAll(
                `[data-passage="${CSS.escape(id)}"] [data-sentence="${index}"]`,
              ),
            ];
          })();
    const ranges = elements.map((element) => {
      const range = document.createRange();
      range.selectNodeContents(element);
      return range;
    });
    if (!ranges.length) return;
    cancelFind.current();
    finding.current = true;
    cancelFind.current = findSentence(
      ranges,
      () => {
        finding.current = false;
        setFoundInPage(true);
      },
      () => {
        finding.current = false;
        setFoundInPage(false);
      },
    );
  };
  useEffect(() => {
    if (!autoFind.current || !pinned || !lockedNode) return;
    autoFind.current = false;
    setFoundInPage(true);
    if (!isExtension) findLocked();
  }, [navigationRequest, lockedNode, pinned]);
  const move = (id: string, pin = false, offset = 0) => {
    if (pinned && !pin) {
      const text =
        artifact?.regions.find((r) => r.id === id)?.anchor.exact ?? "";
      const sentence = sentences(text).find(
        (s) => s.start <= offset && s.end > offset,
      );
      if (
        id !== region ||
        (sentence &&
          !(sentence.start <= sentenceOffset && sentence.end > sentenceOffset))
      )
        blocked(`text:${id}:${sentence?.start ?? 0}`, 2);
      return;
    }
    setRegion(id);
    setSentenceOffset(offset);
    setSourceHover(true);
    setRelatedNode(null);
    setLockedNode(null);
    if (pin) {
      setPinned(true);
      void pageCommand(tabId, artifact, "TOMPATHY_FOCUS", {
        region: id,
        offset,
      });
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
  async function toggleContext(
    enabled: boolean,
    discover = followLinks,
    refresh = false,
    automatic = false,
    github = useGitHub,
  ) {
    collector.current?.abort();
    setContextEnabled(enabled);
    localStorage.setItem("tompathy-context-enabled", String(enabled));
    setContextWork(null);
    setContextReport(null);
    if (!enabled || !artifact) return;
    if (refresh) clearContextCache();
    const request = serial.current;
    const sources = (session.contextSources ?? []).filter(
      (s) => s.author.toLocaleLowerCase() === creatorName.toLocaleLowerCase(),
    );
    const job = new AbortController();
    collector.current = job;
    try {
      const urls = sources.map((s) => contextSourceURL(s.url, github));
      const origins = [
        ...new Set([
          ...urls.map(
            (u) =>
              (github && githubRepository(u.href)
                ? "https://api.github.com"
                : u.origin) + "/*",
          ),
          ...(github &&
          (session.repositoryLinks?.length || (discover && sources.length))
            ? ["https://api.github.com/*"]
            : []),
        ]),
      ];
      const allowed =
        !isExtension ||
        !origins.length ||
        (await (automatic
          ? chrome.permissions.contains({ origins })
          : chrome.permissions.request({ origins })));
      if (request !== serial.current || job.signal.aborted) return;
      setContextWork({
        phase: "working",
        completed: 0,
        total: 1,
        label: "Reading byline",
      });
      const byline = await bylineContext(artifact, creatorName);
      if (request !== serial.current || job.signal.aborted) return;
      if (byline)
        setSession((s) => ({ ...s, context: mergeContext(s.context, byline) }));
      if (!allowed)
        throw Error(
          automatic
            ? "Open Options and refresh context to allow access to these sources."
            : "Context source access was declined.",
        );
      const report = await collectCreatorContext({
        sources,
        repositoryLinks: session.repositoryLinks,
        pageSource: artifact.source,
        existingContext: refresh ? [] : session.context,
        creator: creatorName,
        useGitHub: github,
        followLinks: discover,
        signal: job.signal,
        onResult: (item) => {
          if (request === serial.current && !job.signal.aborted)
            setSession((s) => ({
              ...s,
              context: mergeContext(s.context, item),
            }));
        },
        onProgress: (completed, total, label) => {
          if (request === serial.current && !job.signal.aborted)
            setContextWork({ phase: "working", completed, total, label });
        },
      });
      if (request !== serial.current || job.signal.aborted) return;
      setContextReport(report);
      setContextWork({
        phase:
          report.failures.length || (!byline && !report.collected)
            ? "error"
            : "done",
        completed: report.attempted,
        total: report.attempted || 1,
        label: report.failures.length
          ? "Some context sources were unavailable. Open the timeline for coverage."
          : !sources.length && !(github && session.repositoryLinks?.length)
            ? byline
              ? "Page byline recorded; no explicit creator links found."
              : "No creator byline or explicit public profile links found."
            : "Creator context and timeline collected. A new analysis is needed before estimates change.",
      });
    } catch (e) {
      if (request === serial.current && !job.signal.aborted)
        setContextWork({
          phase: "error",
          completed: 0,
          total: 1,
          label: (e as Error).message,
        });
    }
  }
  const automaticContextKey = useRef("");
  useEffect(() => {
    if (!hydrated || !artifact || !contextEnabled) return;
    const key = `${artifact.id}:${artifact.revision}:${creatorName}:${useGitHub}:${followLinks}`;
    if (automaticContextKey.current === key) return;
    automaticContextKey.current = key;
    void toggleContext(true, followLinks, false, true);
  }, [hydrated, artifact?.id, artifact?.revision, creatorName]);
  function exportReading() {
    try {
      const url = URL.createObjectURL(
        new Blob([readingFile(session)], { type: "text/html" }),
      );
      const a = document.createElement("a");
      a.href = url;
      a.download = "tompathy-reading.html";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
      if (mismatch)
        setNotice(
          "Reading saved. The previous account is retained in history; selected context awaits a matching analysis.",
        );
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function importReading(file?: File) {
    if (!file) return;
    try {
      if (file.size > 12000000)
        throw Error("Reading files must be under 12 MB.");
      const request = serial.current,
        text = await file.text();
      if (request !== serial.current) return;
      if (text.trimStart().startsWith("{") && JSON.parse(text).schemaVersion) {
        await loadPacket(text);
        return;
      }
      const loaded = await parseReadingFile(text);
      if (request !== serial.current) return;
      cancelWork();
      await pageCommand(tabId, artifact, "TOMPATHY_CLEANUP");
      setSession(loaded);
      setStale(false);
      setDetail(null);
      setPinned(false);
      setLockedNode(null);
      setRelatedNode(null);
      setSourceHover(false);
      setRegion(loaded.artifact!.regions[0].id);
      setModal(null);
      setTabId(null);
      if (isExtension) {
        const id = crypto.randomUUID();
        const restored = { ...loaded, savedPageId: id };
        await chrome.storage.session.set({ [`snapshot:${id}`]: restored });
        setSession(restored);
        const tab = await chrome.tabs.create({
          url: chrome.runtime.getURL(`snapshot.html?id=${id}`),
        });
        setTabId(tab.id ?? null);
      }
    } catch (e) {
      setError((e as Error).message);
    }
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
  return (
    <div className={preview ? "workspace" : "extension-root"}>
      {preview && artifact && artifact.source !== "tompathy:example" ? (
        <ReadingPreview
          packet={ready ? packet : null}
          maker={activeMaker?.id}
          lockReminder={lockReminder}
          artifact={artifact}
          region={region}
          offset={sentenceOffset}
          pinned={pinned}
          active={pinned || sourceHover}
          onMove={move}
          onLeave={() => {}}
          onUnlock={unlock}
        />
      ) : (
        preview && (
          <ExampleArticle
            packet={ready ? packet : null}
            maker={activeMaker?.id}
            lockReminder={lockReminder}
            active={
              pinned || sourceHover || relatedNode?.span
                ? (relatedNode?.span?.region ?? region)
                : ""
            }
            pinned={pinned}
            related={
              (relatedNode?.span ? [] : relatedNode?.regions) ??
              (lockedNode?.span ? undefined : lockedNode?.regions) ??
              detail?.regions ??
              []
            }
            sentenceOffset={relatedNode?.span?.start ?? sentenceOffset}
            onUnlock={unlock}
            onLeave={() => {}}
            onMove={move}
          />
        )
      )}
      <div
        className="reader"
        data-tompathy-ui
        onPointerLeave={() => {
          if (pinned && tour === -1) setTour(null);
        }}
      >
        {new URLSearchParams(location.search).has("qa") && (
          <button className="qa-entry" onClick={() => setModal("qa")}>
            Development tools
          </button>
        )}
        {tour !== null && (
          <div className="interaction-guide" role="status">
            <span>
              {tour === -1
                ? "New here? Try a brief interaction guide."
                : [
                    "Move over a sentence in the page. Watch attention and the reels change.",
                    "Click that sentence to hold it. You can now move into the reader.",
                    "Hover a reel to reveal its possible paths. Scroll to choose another goal.",
                    "Click either green lock, or double-click anywhere in the page or reader, to let go. You can replay this guide from Help.",
                  ][tour]}
            </span>
            <button onClick={() => setTour(tour === 3 ? null : tour + 1)}>
              {tour === -1 ? "Show me" : tour === 3 ? "Done" : "Next"}
            </button>
            <button
              aria-label="Dismiss interaction guide"
              onClick={() => setTour(null)}
            >
              <X size={14} />
            </button>
          </div>
        )}
        <div className={`reader-content ${ready ? "is-ready" : ""}`}>
          <section
            className="region goals-region"
            aria-labelledby="goals-title"
          >
            <div className="section-heading">
              <SectionTitle
                kind="goals"
                onOpen={() => openSectionHelp("goals")}
              >
                Current attention
              </SectionTitle>
              <label className="creator-control">
                <img className="creator-brain" src="./icon128.png" alt="" />
                <span className="sr-only">Creator selection</span>
                <span className="creator-choice">
                  <select
                    title={creatorName}
                    value={
                      ready
                        ? activeMaker?.id
                        : (session.authorLabel ?? creatorName)
                    }
                    onChange={(e) => {
                      setMaker(e.target.value);
                      setDetail(null);
                      setContextWork(null);
                      setContextReport(null);
                      collector.current?.abort();
                      if (!ready)
                        setSession((s) => ({
                          ...s,
                          authorLabel: e.target.value,
                        }));
                    }}
                  >
                    {ready ? (
                      packet!.makers.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.label}
                        </option>
                      ))
                    ) : artifact?.authors?.length ? (
                      artifact.authors.map((a) => (
                        <option key={a.label}>{a.label}</option>
                      ))
                    ) : (
                      <option>{creatorName}</option>
                    )}
                  </select>
                  <span className="creator-current" aria-hidden="true">
                    <span>{creatorName}</span>
                    <svg viewBox="0 0 12 12" width="9" height="9">
                      <path
                        d="M3 4.5 6 7.5 9 4.5"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.1"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                </span>
              </label>
            </div>
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
                <IconButton
                  label="Dismiss notice"
                  onClick={() => setNotice("")}
                >
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
                    onClick={() =>
                      stale ? void capture() : setModal("import")
                    }
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
                <button
                  className="primary-button"
                  onClick={() => void example()}
                >
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
            {ready && (
              <GoalCloud
                key={packet!.id}
                goals={goals}
                active={
                  !!attentionTarget ||
                  !!attentionNode ||
                  !packet?.currentAttention?.length
                }
                onInspect={inspect}
              />
            )}
          </section>
          <section
            className="region process-region"
            aria-labelledby="process-title"
          >
            <div className="section-heading">
              <SectionTitle
                kind="process"
                onOpen={() => openSectionHelp("process")}
              >
                Expertise and habit (previous attention)
              </SectionTitle>
            </div>
            {ready &&
            packet &&
            !hierarchyNodes.length &&
            packet.process.nodes.length > 0 ? (
              <RecordedProcess
                packet={packet}
                maker={activeMaker?.id}
                inspect={inspect}
              />
            ) : (
              <ProcessHierarchy
                lockReminder={lockReminder}
                onBlockedFocus={blocked}
                key={`${packet?.id}:${packet?.revision}:${activeMaker?.id}`}
                nodes={hierarchyNodes}
                orderUncertainGroups={
                  ready ? packet?.goalHierarchy?.orderUncertainGroups : []
                }
                region={region}
                offset={sentenceOffset}
                sourceHover={sourceHover}
                softNodeId={relatedNode?.id}
                pinned={pinned}
                lockedNodeId={lockedNode?.id}
                onSelect={(node) => {
                  autoFind.current = true;
                  setNavigationRequest((n) => n + 1);
                  setFoundInPage(true);
                  setLockedNode(node);
                  setPinned(true);
                  setRelatedNode(null);
                  setRegion(node.regions[0]);
                  setSentenceOffset(node.span?.start ?? 0);
                  void pageCommand(tabId, artifact, "TOMPATHY_FOCUS", {
                    region: node.regions[0],
                    offset: node.span?.start ?? 0,
                    regions: node.span ? undefined : node.regions,
                    center: true,
                  });
                }}
                onHighlight={(node) => {
                  if (pinned || !node) return;
                  setSourceHover(false);
                  setRelatedNode(node);
                  void pageCommand(tabId, artifact, "TOMPATHY_RELATED", {
                    regions: node?.regions ?? [],
                    span: node?.span,
                  });
                }}
                onLock={unlock}
                onFind={findLocked}
                found={foundInPage}
              />
            )}
          </section>
          <section
            className="region values-region"
            aria-labelledby="values-title"
          >
            <div className="section-heading">
              <SectionTitle
                kind="values"
                onOpen={() => openSectionHelp("values")}
              >
                Core values
              </SectionTitle>
            </div>
            <div
              id="values-view"
              role="tabpanel"
              aria-label={
                valuesTab === "work"
                  ? "Current work only values"
                  : valuesTab === "creator"
                    ? "Creator values"
                    : "Global population values"
              }
            >
              {ready && valuesTab === "global" && packet?.population ? (
                <PopulationValues packet={packet} maker={activeMaker?.id} />
              ) : (
                <ValueList
                  values={
                    valuesTab === "work"
                      ? demoWorkValues(ready ? packet : null, values)
                      : valuesTab === "creator"
                        ? values
                        : demoGlobalValues(ready ? packet : null, values)
                  }
                  packet={packet}
                  inspect={inspect}
                />
              )}
              {ready &&
                valuesTab === "creator" &&
                activeMaker?.predictability && (
                  <p className="predictability-note">
                    Predictability:{" "}
                    {activeMaker.predictability.value.toFixed(2)} on{" "}
                    {activeMaker.predictability.scale.join("–")}.{" "}
                    {activeMaker.predictability.meaning}
                  </p>
                )}
            </div>
            <div className="values-bottom">
              <ValueTabs tab={valuesTab} onTab={setValuesTab} />
              <ContextProgress work={contextWork} />
              <IconButton label="Reader menu" onClick={() => setModal("menu")}>
                <MoreHorizontal size={18} />
              </IconButton>
            </div>
          </section>
          <span className="sr-only" role="status">
            {busy
              ? "Capturing"
              : ready
                ? `${creatorName}. ${packet!.origin}. ${pinned ? "Locked" : "Following"} ${region}, sentence offset ${sentenceOffset}.`
                : artifact
                  ? "Awaiting analysis"
                  : "Choose a text"}
          </span>
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
            {detail.kind === "value" && detail.preferenceTrace ? (
              <ValueDetails h={detail} packet={packet} />
            ) : (
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
                  Creator: {activeMaker?.label} · {activeMaker?.relationship}
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
                        {packet!.hypotheses.find((h) => h.id === e.from)!.label}{" "}
                        → {packet!.hypotheses.find((h) => h.id === e.to)!.label}
                        : {e.relationship}.{" "}
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
                              packet!.hypotheses.find((h) => h.id === id)!
                                .label,
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
            )}
          </Modal>
        )}
      </div>
      {modal && (
        <Modal
          title={
            {
              menu: "Options",
              qa: "Development tools",
              context: "Build the context",
              "creator-context": "Creator context",
              source: "The source text",
              settings: "Your reader",
              import: "Connect an analysis",
              help: "A little closer to the creator",
              revision: "Review the new perspective",
              history: "Earlier accounts",
              claims: "All supplied hypotheses",
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
          {modal === "creator-context" && (
            <ContextTimeline
              items={context}
              creator={creatorName}
              report={contextReport}
              busy={contextWork?.phase === "working"}
              onCancel={() => {
                collector.current?.abort();
                setContextEnabled(false);
                setContextWork(null);
              }}
              onRefresh={() => void toggleContext(true, followLinks, true)}
              onClear={() => {
                collector.current?.abort();
                clearContextCache();
                setContextEnabled(false);
                setContextReport(null);
                setContextWork(null);
                setSession((s) => ({ ...s, context: [], scope: "artifact" }));
              }}
              onSelect={(id, selected) =>
                setSession((s) => {
                  const context = s.context.map((c) =>
                    c.id === id ? { ...c, selected } : c,
                  );
                  return {
                    ...s,
                    scope: context.some((c) => c.selected)
                      ? "context"
                      : "artifact",
                    context,
                  };
                })
              }
            />
          )}
          {modal === "menu" && (
            <div className="options-content">
              <ProviderOptions
                settings={provider}
                onSave={(next) => {
                  analyzer.current?.abort();
                  setProvider(next);
                }}
              />
              {provider.kind !== "none" && (
                <div className="analysis-actions">
                  <button
                    className="secondary-button"
                    disabled={!artifact || busy || stale || analyzing}
                    onClick={() => {
                      setModal(null);
                      void analyze();
                    }}
                  >
                    {analyzing ? "Analyzing capture…" : "Analyze capture"}
                  </button>
                  {provider.kind === "local" &&
                    artifact &&
                    /^https:\/\/[a-z0-9-]+\.wikipedia\.org\/wiki\/[^?#]+$/i.test(
                      artifact.source,
                    ) && (
                      <button
                        className="secondary-button"
                        disabled={
                          busy || stale || analyzing || scope !== "artifact"
                        }
                        title="Fetch public Wikipedia revisions and analyze their recorded changes. Uses the work-only scope."
                        onClick={() => {
                          setModal(null);
                          void analyze("wikipedia");
                        }}
                      >
                        Analyze Wikipedia history
                      </button>
                    )}
                  {analyzing && (
                    <button
                      className="text-button"
                      onClick={() => {
                        analyzer.current?.abort();
                        setAnalyzing(false);
                      }}
                    >
                      Cancel analysis
                    </button>
                  )}
                </div>
              )}
              <section
                className="options-section context-options"
                aria-labelledby="context-options-title"
              >
                <h3 id="context-options-title">Context</h3>
                <label className="option-check">
                  <input
                    type="checkbox"
                    checked={contextEnabled}
                    onChange={(e) => void toggleContext(e.target.checked)}
                  />
                  <span>
                    Light context
                    <small>
                      Read the byline and follow the creator’s explicit profile
                      links.
                    </small>
                  </span>
                </label>
                <div className="nested-options">
                  <label className="option-check">
                    <input
                      type="checkbox"
                      checked={followLinks}
                      onChange={(e) => {
                        setFollowLinks(e.target.checked);
                        localStorage.setItem(
                          "tompathy-follow-links",
                          String(e.target.checked),
                        );
                        if (contextEnabled)
                          void toggleContext(true, e.target.checked);
                      }}
                    />
                    <span>
                      Agent search
                      <small>
                        Follow linked pages and feeds on the permitted sites.
                        Build a dated timeline locally, without an AI model or
                        paid search.
                      </small>
                    </span>
                  </label>
                  <label className="option-check">
                    <input
                      type="checkbox"
                      checked={useGitHub}
                      onChange={(e) => {
                        setUseGitHub(e.target.checked);
                        localStorage.setItem(
                          "tompathy-use-github",
                          String(e.target.checked),
                        );
                        if (contextEnabled)
                          void toggleContext(
                            true,
                            followLinks,
                            false,
                            false,
                            e.target.checked,
                          );
                      }}
                    />
                    <span>
                      Use GitHub when possible
                      <small>
                        Read explicitly linked profiles, repositories and
                        source-file revisions. No paid API or model.
                      </small>
                    </span>
                  </label>
                </div>
                <button
                  className="context-view-button"
                  onClick={() => setModal("creator-context")}
                >
                  View context and timeline
                </button>
              </section>
              <section
                className="options-section future-options"
                aria-label="Future analysis"
              >
                <label className="option-check future">
                  <input type="checkbox" disabled />
                  <span>
                    Create a small local model to think like this creator
                    <small>Planned · no model is created yet.</small>
                  </span>
                </label>
                <label className="option-check future">
                  <input type="checkbox" disabled />
                  <span>
                    Word-level analysis
                    <small>
                      Word-level analysis is potentially academically
                      interesting but difficult to interpret.
                    </small>
                  </span>
                </label>
              </section>
              <section
                className="color-scheme"
                aria-labelledby="color-scheme-title"
              >
                <h3 id="color-scheme-title">Color scheme</h3>
                <div
                  className="theme-options"
                  role="group"
                  aria-label="Color scheme"
                >
                  {["system", "light", "dark"].map((t) => (
                    <button
                      key={t}
                      aria-pressed={theme === t}
                      onClick={() => {
                        setTheme(t);
                        void writeTheme(t);
                      }}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </section>
              <footer className="options-footer">
                <button onClick={() => setModal("help")}>
                  <CircleHelp size={15} /> <span>How ToMpathy works</span>
                </button>
                <div>
                  <label
                    className="options-import"
                    title="Import a saved reading or matching analysis"
                  >
                    <Upload size={15} />
                    <span>Import</span>
                    <input
                      type="file"
                      accept=".html,.json"
                      aria-label="Import reading"
                      onChange={(e) => {
                        void importReading(e.target.files?.[0]);
                        e.target.value = "";
                      }}
                    />
                  </label>
                  <button disabled={!artifact} onClick={exportReading}>
                    <Download size={15} />
                    <span>Export</span>
                  </button>
                </div>
              </footer>
            </div>
          )}
          {modal === "qa" && (
            <nav className="reader-menu" aria-label="Development tools">
              {(
                [
                  ["claims", "All supplied hypotheses"],
                  ["source", "Source text"],
                  ["context", "Context"],
                  ["import", "Import result"],
                  ["settings", "Reader settings"],
                  ["history", "Earlier accounts"],
                ] as const
              ).map(([id, label]) => (
                <button key={id} onClick={() => setModal(id)}>
                  {label}
                </button>
              ))}
            </nav>
          )}
          {modal === "claims" && (
            <>
              <p>
                Goals, historical process accounts and latent preferences retain
                their supplied meanings. Historical edges are not treated as a
                goal hierarchy.
              </p>
              <div className="all-claims">
                {hypotheses.map((h) => (
                  <button
                    key={h.id}
                    className="hypothesis list"
                    onClick={() => {
                      setModal(null);
                      inspect(h);
                    }}
                  >
                    <span>
                      {h.label}
                      <small>{interpretationLabel(h)}</small>
                    </span>
                    <ChevronRight size={14} />
                  </button>
                ))}
              </div>
            </>
          )}
          {modal === "help" && (
            <>
              <p className="modal-lead">What's on the creator's mind?</p>
              <button
                className="secondary-button"
                onClick={() => {
                  setModal(null);
                  setTour(0);
                }}
              >
                Try the interaction guide <MousePointer2 size={15} />
              </button>
              <ol className="steps">
                <li>
                  <strong>Follow a sentence.</strong> Hover page text to roll
                  through its goal hierarchy. Click to lock it; double-click
                  anywhere in the page or reader to release it. The green lock
                  also releases it; Escape closes an open overlay first. Native
                  text selection and links still work. Use Tab to focus
                  hierarchy blocks and values; the reels support arrow-key
                  selection.
                </li>
                <li>
                  <strong>Explore the shape.</strong> The continuous hierarchy
                  stays visible above the reels. Hover or focus a block: its
                  ancestors light up to the right, its descendants fan out to
                  the left, and the matching page text shares their color.
                  Blurred spools mean several subordinate goals, broader goals
                  or earlier endings remain possible.
                </li>
                <li>
                  <strong>Look closer.</strong> Hover or focus headings, goals
                  and values for explanations. Select a goal or value for the
                  full evidence account.
                </li>
              </ol>
              <h3 id="help-goals">Current attention</h3>
              <p>{explanations.goals}</p>
              <h3 id="help-process">
                Expertise and habit (previous attention)
              </h3>
              <p>{explanations.process}</p>
              <h3 id="help-values">Core values</h3>
              <p>{explanations.values}</p>
              <h3>Reading the text</h3>
              <p>
                Sentence ink follows the supplied Ghost Scale account: full ink
                for creator-written text, 95% opacity for light AI edits,
                readable grey for curated material, and reversed colours for
                unreviewed generation. Grey is adjusted to retain at least 4.5:1
                contrast against its surface. Existing bold becomes an
                underline. Stroke grade shows confidence in that classification;
                it does not measure truth or quality. Pause over a sentence, or
                focus it with Tab, to inspect its evidence. Missing information
                leaves the original styling alone.
              </p>
              <h3>This account</h3>
              <p>
                {packet
                  ? `${creatorName} · ${packet.origin}. ${packet.provider.method}.`
                  : "No analysis is connected. Ordinary pages await a supplied result."}{" "}
                The bundled example is fictional and hand-written. Older packets
                without a goal hierarchy remain readable in the source and
                evidence tools; a hierarchy is never inferred from historical
                process edges.
              </p>
              <p>
                Reduced-motion settings are respected. Word-level goals are
                reserved for a later version. Context collection alone never
                changes the accepted account.
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
                Creator to inspect
                <input
                  value={
                    session.authorLabel ??
                    (artifact?.authors?.length === 1
                      ? artifact.authors[0].label
                      : "")
                  }
                  maxLength={250}
                  placeholder="Creator not identified"
                  onChange={(e) =>
                    setSession((s) => ({ ...s, authorLabel: e.target.value }))
                  }
                />
              </label>
              <p className="muted">
                {ready
                  ? `Analysis subject: ${activeMaker?.label}. Editing the requested creator does not reassign existing claims.`
                  : "A page byline is a source attribution, not a verified identity. You can correct the requested creator before exporting."}
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
                establish what the creator knew or believed.
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
              <h3>Analysis detail</h3>
              <label className="future-option">
                <input type="checkbox" disabled /> Word-level goals{" "}
                <small>
                  Planned · sentence-level reading is available now.
                </small>
              </label>
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
  packet = null,
  maker,
  lockReminder = 0,
  active = "",
  pinned = false,
  related = [],
  onMove = () => {},
  onLeave = () => {},
  onUnlock = () => {},
  sentenceOffset = 0,
}: {
  packet?: Packet | null;
  maker?: string;
  lockReminder?: number;
  active?: string;
  pinned?: boolean;
  related?: string[];
  onMove?: (id: string, pin?: boolean, offset?: number) => void;
  onLeave?: () => void;
  onUnlock?: () => void;
  sentenceOffset?: number;
}) {
  const standalone = isExtension && location.pathname.endsWith("example.html");
  const pointedOffset = (
    el: HTMLElement,
    x: number,
    y: number,
    sentence: { start: number; text: string },
  ) => {
    return sentence.start + textOffset(el, x, y, sentence.text.length);
  };
  return (
    <div className="example-page">
      <nav>
        <span className="journal-mark">
          FIELDNOTES<span>ON EVERYDAY DESIGN</span>
        </span>
        <span className="journal-issue">
          No. 015 <span>—</span> Play & people
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
              if (tab?.id) {
                await chrome.sidePanel.setOptions({
                  path: new URLSearchParams(location.search).has("qa")
                    ? "panel.html?qa"
                    : "panel.html",
                  enabled: true,
                });
                await chrome.sidePanel.open({ tabId: tab.id });
              }
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
      <article onMouseLeave={onLeave}>
        <div className="article-kicker" data-tompathy-ui>
          SMALL INTERVENTIONS / 04 MIN READ
        </div>
        <h1
          data-passage="p1"
          onMouseMove={() => onMove("p1")}
          onClick={() =>
            !window.getSelection()?.toString() && onMove("p1", true)
          }
        >
          {exampleText[0]}
        </h1>
        <div className="article-deck" data-tompathy-ui>
          Two players, one stubborn door,
          <br />
          and a lesson in waiting.
        </div>
        <div className="article-byline" data-tompathy-ui>
          <span className="creator-avatar">M</span>
          <span>
            Mara Vale <small>September 14, 2026 · Fictional creator</small>
          </span>
          <span className="article-rule" />
        </div>
        {exampleText.slice(1).map((text, i) => (
          <p
            key={i}
            data-passage={`p${i + 2}`}
            tabIndex={0}
            className={`${active === `p${i + 2}` ? "active-passage" : ""} ${related.includes(`p${i + 2}`) ? "related-passage" : ""}`}

            onFocus={(e) => {
              if (e.target === e.currentTarget) onMove(`p${i + 2}`);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                const sentence = (e.target as HTMLElement).closest<HTMLElement>(
                  "[data-sentence]",
                );
                onMove(
                  `p${i + 2}`,
                  true,
                  sentence
                    ? sentences(text)[Number(sentence.dataset.sentence)].start
                    : 0,
                );
              }
            }}
          >
            <span className="passage-number" aria-hidden="true">
              {String(i + 1).padStart(2, "0")}
              {pinned && active === `p${i + 2}` ? " ·" : ""}
            </span>
            {standalone ? (
              <ReadingText
                text={text}
                emphasis={exampleEmphasis(`p${i + 2}`, text)}
                annotate={false}
              />
            ) : (
              sentences(text).map((sentence, j) => (
                <span
                  key={j}
                  data-sentence={j}
                  tabIndex={0}
                  onFocus={() => onMove(`p${i + 2}`, false, sentence.start)}
                  className={
                    active === `p${i + 2}` &&
                    sentenceOffset >= sentence.start &&
                    sentenceOffset < sentence.end
                      ? "active-sentence"
                      : ""
                  }
                  onMouseMove={(e) => {
                    if ((e.target as Element).closest("button")) return;
                    onMove(
                      `p${i + 2}`,
                      false,
                      pointedOffset(
                        e.currentTarget,
                        e.clientX,
                        e.clientY,
                        sentence,
                      ),
                    );
                  }}
                  onClick={(e) =>
                    !window.getSelection()?.toString() &&
                    onMove(
                      `p${i + 2}`,
                      true,
                      pointedOffset(
                        e.currentTarget,
                        e.clientX,
                        e.clientY,
                        sentence,
                      ),
                    )
                  }
                >
                  <ReadingText
                    text={sentence.text}
                    start={sentence.start}
                    emphasis={exampleEmphasis(`p${i + 2}`, text)}
                    reading={ghostAt(
                      packet,
                      maker,
                      `p${i + 2}`,
                      sentence.start,
                      sentence.end,
                    )}
                    packet={packet}
                  />
                  {pinned &&
                    active === `p${i + 2}` &&
                    sentenceOffset >= sentence.start &&
                    sentenceOffset < sentence.end && (
                      <SelectionLock
                        reminder={lockReminder}
                        className="inline-lock"
                        onUnlock={onUnlock}
                      />
                    )}
                  {j < sentences(text).length - 1 ? " " : ""}
                </span>
              ))
            )}
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
