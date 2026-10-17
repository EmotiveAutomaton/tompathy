import { findSentence } from "./find-sentence";
import { selectionTransition } from "./selection-transition";
import { textPoints, annotatePage } from "./page-reading";
import { attachReadingHelp } from "./reading-help";
import {
  LOCK_SVG,
  LOCK_INK,
  LOCK_BACKGROUND,
  blockedFocusTracker,
  pulseLock,
} from "./core/lock";
import { regionSentences } from "./core/sentences";
import { makeArtifact, normalize } from "./core/artifact";
import {
  SessionSchema,
  type Artifact,
  type Packet,
  type Session,
} from "./core/model";
import {
  pageCreators,
  pageCreatorSources,
  pageRepositoryLinks,
  readingRoot,
} from "./core/page";
import { contributionExplanation } from "./core/reading";
import { isWebsiteDemo } from "./core/site-demo-scope";
import { pageEssay } from "./core/page-essay";
declare global {
  interface Window {
    __tompathyCleanup?: () => void;
    __tompathySnapshot?: Session;
  }
}
export function installPageAdapter() {
  let restored =
    location.protocol === "chrome-extension:" &&
    location.pathname === "/snapshot.html"
      ? window.__tompathySnapshot
      : undefined;
  window.__tompathyCleanup?.();
  let artifact: Artifact | null = null,
    elements: HTMLElement[] = [],
    index = new WeakMap<Element, string>(),
    byId = new Map<string, HTMLElement>(),
    pinned = false,
    selected = "",
    selectedOffset = 0,
    stale = false,
    timer: ReturnType<typeof setTimeout> | undefined;
  const abort = new AbortController(),
    sheet = new CSSStyleSheet();
  const transition = selectionTransition();
  const essay = pageEssay();
  window.addEventListener("scroll", () => transition.clear(), {
    capture: true,
    passive: true,
    signal: abort.signal,
  });
  let ownTabId: number | undefined;
  let removeReading = () => {};
  const removeHelp = attachReadingHelp(document, true);
  const font = new FontFace(
    "ToMpathy Reading",
    `url("${chrome.runtime.getURL("reader-grade.woff")}")`,
  );
  let fontRequested = false;
  const ensureFont = () => {
    if (fontRequested) return;
    fontRequested = true;
    void font
      .load()
      .then((f) => {
        if (!abort.signal.aborted) {
          document.fonts.add(f);
          positionMarker();
        }
      })
      .catch(() => {});
  };
  const originalTitles = new Map<HTMLElement, string | null>();
  if (location.protocol === "chrome-extension:")
    void chrome.tabs.getCurrent().then((tab) => {
      ownTabId = tab?.id;
    });
  sheet.replaceSync(`
    ::highlight(tompathy-active){background-color:#56867444;color:inherit}
    ::highlight(tompathy-related){background-color:#56867432;color:inherit}
    [data-tompathy-related]{background-color:#56867425 !important;border-radius:3px}
  `);
  const highlights = (CSS as any).highlights;
  const ranges = new Map<
    string,
    { start: number; end: number; range: Range }[]
  >();
  let pointOffsets = new WeakMap<Node, number[]>();
  const marker = document.createElement("button");
  const blockedFocus = blockedFocusTracker();
  let cancelPulse = () => {};
  const remind = () => {
    if (!pinned) return;
    cancelPulse();
    blockedFocus.acknowledge(performance.now());
    cancelPulse = pulseLock(marker);
  };
  marker.type = "button";
  marker.setAttribute("data-tompathy-ui", "");
  marker.setAttribute("aria-label", "Unlock selection");
  marker.title = "Unlock selection · Escape";
  marker.innerHTML = LOCK_SVG;
  marker.style.cssText = `all:initial;box-sizing:border-box;position:fixed;z-index:2147483647;cursor:pointer;width:23px;height:23px;align-items:center;justify-content:center;color:${LOCK_INK};background:${LOCK_BACKGROUND};border:1px solid #c7d8ca;border-radius:50%;padding:0;box-shadow:0 1px 3px #426f5d10;display:none`;
  document.documentElement.append(marker);
  const paint = (name: string, rs: Range[]) => {
    if (highlights && (globalThis as any).Highlight)
      highlights.set(name, new (globalThis as any).Highlight(...rs));
  };
  const positionMarker = () => {
    const selectedRange = ranges
      .get(selected)
      ?.find((s) => s.start <= selectedOffset && s.end > selectedOffset)?.range;
    const rects = selectedRange?.getClientRects();
    const r = rects?.[rects.length - 1];
    marker.style.display =
      pinned && r && r.bottom > 0 && r.top < innerHeight ? "grid" : "none";
    if (r) {
      marker.style.left = `${Math.max(1, Math.min(innerWidth - 24, r.right - 5))}px`;
      marker.style.top = `${Math.max(1, Math.min(innerHeight - 24, r.bottom - 5))}px`;
    }
  };
  window.addEventListener("scroll", positionMarker, {
    capture: true,
    passive: true,
    signal: abort.signal,
  });
  window.addEventListener("resize", positionMarker, { signal: abort.signal });
  document.adoptedStyleSheets = [...document.adoptedStyleSheets, sheet];
  const clear = () => {
    transition.clear();
    removeReading();
    removeReading = () => {};
    blockedFocus.reset();
    cancelPulse();
    highlights?.delete("tompathy-active");
    highlights?.delete("tompathy-related");
    marker.style.display = "none";
    elements.forEach((el) => {
      for (const name of ["mark", "selected", "uncertain", "related"])
        el.removeAttribute(`data-tompathy-${name}`);
      el.style.removeProperty("--tompathy-tint");
      if (originalTitles.has(el)) {
        const title = originalTitles.get(el);
        if (title === null) el.removeAttribute("title");
        else el.setAttribute("title", title!);
        originalTitles.delete(el);
      }
    });
  };
  const excluded =
    (isWebsiteDemo(location.href) ? "" : "nav,header,footer,aside,") +
    (location.hostname.endsWith(".wikipedia.org")
      ? ".reflist,.mw-references-wrap,.navbox,.metadata,.mw-editsection,.catlinks,"
      : "") +
    '[role="tooltip"],.citation-tooltip-portal,[popover],button,input,textarea,select,script,style,.katex,.art-latex-loading,[contenteditable]:not([contenteditable="false"]),[hidden],[aria-hidden="true"],[data-tompathy-ui],.entryFooter,.entry-footer,.post-footer,.related,.related-posts,.recent-articles,.subscription,.newsletter,.comments,#comments';
  const readable = (el: HTMLElement) => {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let text = "",
      node: Node | null;
    while ((node = walker.nextNode())) {
      const parent = node.parentElement;
      if (
        parent &&
        !parent.closest(excluded) &&
        parent.checkVisibility({ checkVisibilityCSS: true })
      )
        text += node.textContent ?? "";
    }
    return normalize(text);
  };
  const eligible = (el: HTMLElement) =>
    !el.closest(excluded) &&
    el.checkVisibility({ checkVisibilityCSS: true }) &&
    readable(el).length >=
      (isWebsiteDemo(location.href) ||
      (location.protocol === "chrome-extension:" &&
        location.pathname === "/art.html" &&
        el.hasAttribute("data-passage"))
        ? 1
        : 12);
  const blockSelector = "h1,h2,h3,h4,p,li,blockquote,pre,dd,dt,td";
  const captureElements = (root: Element) => {
    const groups = isWebsiteDemo(location.href)
      ? Array.from(root.querySelectorAll<HTMLElement>("footer")).filter(
          eligible,
        )
      : [];
    const candidates = Array.from(
      root.querySelectorAll<HTMLElement>(blockSelector),
    ).filter(
      (el) => eligible(el) && !groups.some((group) => group.contains(el)),
    );
    candidates.push(...groups);
    if (isWebsiteDemo(location.href)) {
      // The portfolio's project descriptions are plain divs rather than p tags.
      // Include text leaves, never whole containers that would duplicate children.
      candidates.push(
        ...Array.from(root.querySelectorAll<HTMLElement>("div,section")).filter(
          (el) =>
            eligible(el) &&
            !groups.some((group) => group.contains(el)) &&
            !el.querySelector(
              `div,section,${blockSelector},button,canvas,svg`,
            ) &&
            Array.from(el.childNodes).some(
              (n) =>
                (n.nodeType === Node.TEXT_NODE && !!n.textContent?.trim()) ||
                (n instanceof HTMLElement &&
                  n.hasAttribute("data-tompathy-reading")),
            ),
        ),
      );
      candidates.sort((a, b) =>
        a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING
          ? -1
          : 1,
      );
    }
    const set = new Set(candidates);
    return candidates.filter(
      (el) =>
        !Array.from(el.querySelectorAll(blockSelector)).some((other) =>
          set.has(other as HTMLElement),
        ),
    );
  };
  const send = (type: string, data: object = {}) => {
    try {
      void chrome.runtime
        .sendMessage({
          type,
          sourceTabId: ownTabId,
          documentId: artifact?.id,
          revision: artifact?.revision,
          ...data,
        })
        .catch(() => {});
    } catch {
      /* extension reloaded */
    }
  };
  let cancelFind = () => {};
  let findAcknowledged = false;
  const release = () => {
    const focused = document.activeElement as HTMLElement | null;
    if (focused?.matches("[data-tompathy-help],[data-tompathy-reading]"))
      focused.blur();
    transition.clear();
    cancelFind();
    findAcknowledged = false;
    blockedFocus.reset();
    cancelPulse();
    pinned = false;
    highlights?.delete("tompathy-active");
    highlights?.delete("tompathy-related");
    elements.forEach((el) => {
      el.removeAttribute("data-tompathy-related");
      el.removeAttribute("data-tompathy-selected");
    });
    selected = "";
    selectedOffset = 0;
    positionMarker();
    send("TOMPATHY_UNLOCK");
  };
  marker.addEventListener(
    "click",
    (e) => {
      e.stopPropagation();
      release();
    },
    { signal: abort.signal },
  );
  const select = (id: string, pin = false, notify = true, offset = 0) => {
    if (stale) return;
    const sentence =
      ranges.get(id)?.find((s) => s.start <= offset && s.end > offset) ??
      ranges.get(id)?.[0];
    if (!pin && pinned) {
      if (
        (id !== selected ||
          (sentence &&
            !(
              sentence.start <= selectedOffset && sentence.end > selectedOffset
            ))) &&
        blockedFocus.attempt(
          `text:${id}:${sentence?.start ?? 0}`,
          performance.now(),
          2,
        )
      ) {
        remind();
        send("TOMPATHY_LOCK_REMINDER");
      }
      return;
    }
    if (pin) {
      cancelFind();
      findAcknowledged = false;
      blockedFocus.reset();
      cancelPulse();
    }
    byId.get(selected)?.removeAttribute("data-tompathy-selected");
    selected = id;
    selectedOffset = sentence
      ? Math.max(sentence.start, Math.min(offset, sentence.end - 1))
      : 0;
    if (pin) pinned = true;
    byId.get(id)?.setAttribute("data-tompathy-selected", "");
    paint("tompathy-active", sentence ? [sentence.range] : []);
    if (sentence) transition.show(sentence.range, `${id}:${sentence.start}`);
    highlights?.delete("tompathy-related");
    elements.forEach((el) => el.removeAttribute("data-tompathy-related"));
    positionMarker();
    if (notify)
      send("TOMPATHY_SELECT", { region: id, offset: selectedOffset, pinned });
  };
  const leave = () => {
    // Soft hold: crossing whitespace must not clear the last inspected sentence.
    // Explicit release, navigation and stale-source cleanup still clear it.
  };
  let themeChanged = false;
  const observer = new MutationObserver((records) => {
    if (!artifact || stale || !records.length) return;
    themeChanged ||= records.some(
      (record) => record.attributeName === "data-theme",
    );
    clearTimeout(timer);
    timer = setTimeout(() => {
      // Hover classes and our own affordances are not new text. Theme changes
      // do need fresh annotation colors even when the source text is unchanged.
      // Opening a details element or adding a project dialog is new readable content.
      const now = observedRoot && captureElements(observedRoot);
      if (
        !themeChanged &&
        now &&
        now.length === elements.length &&
        now.every(
          (el, i) =>
            el === elements[i] &&
            readable(el) === artifact?.regions[i]?.anchor.exact,
        )
      )
        return;
      stale = true;
      observer.disconnect();
      clear();
      send("TOMPATHY_STALE");
    }, 200);
  });
  let observedRoot: Element | null = null;
  const observeSource = () => {
    if (!observedRoot) return;
    // The live site's theme switch and project dialogs sit outside its article.
    observer.observe(
      isWebsiteDemo(location.href) ? document.body : observedRoot,
      {
        subtree: true,
        childList: true,
        characterData: true,
        attributes: true,
        attributeFilter: [
          "hidden",
          "aria-hidden",
          "class",
          "open",
          "data-theme",
        ],
      },
    );
  };
  const reindex = () => {
    ranges.clear();
    pointOffsets = new WeakMap();
    for (const [id, el] of byId) {
      const points = textPoints(el, excluded);
      points.forEach((p, i) => {
        const offsets = pointOffsets.get(p.node) ?? [];
        offsets[p.offset] = i;
        pointOffsets.set(p.node, offsets);
      });
      const text = artifact!.regions.find((r) => r.id === id)!.anchor.exact;
      ranges.set(
        id,
        regionSentences(artifact!.regions.find((r) => r.id === id)!).flatMap(
          (s) => {
            const start = points[s.start],
              end = points[s.end - 1];
            if (!start || !end) return [];
            const range = document.createRange();
            range.setStart(start.node, start.offset);
            range.setEnd(end.node, end.offset + 1);
            return [{ start: s.start, end: s.end, range }];
          },
        ),
      );
    }
  };
  const capture = async () => {
    clearTimeout(timer);
    observer.disconnect();
    clear();
    pinned = false;
    selected = "";
    stale = false;
    if (restored?.savedPageId) {
      const key = `snapshot:${restored.savedPageId}`;
      const latest = (await chrome.storage.session.get(key))[key];
      const parsed = SessionSchema.safeParse(latest);
      if (parsed.success) {
        restored = parsed.data;
        window.__tompathySnapshot = restored;
      }
    }
    const resolved = readingRoot(document);
    const root = isWebsiteDemo(location.href) ? document.body : resolved.root;
    const captureInfo = resolved.capture;
    const candidates = captureElements(root);
    elements = candidates.slice(0, 1500);
    if (!elements.length)
      elements = Array.from(root.querySelectorAll<HTMLElement>("div,section"))
        .filter((el) => eligible(el) && !el.querySelector("div,section,p"))
        .slice(0, 1500);
    if (restored?.artifact)
      elements = [
        ...document.querySelectorAll<HTMLElement>("[data-snapshot-region]"),
      ];
    if (!elements.length)
      throw Error("No readable text found. Paste an excerpt to continue.");
    let length = 0;
    elements = elements.filter((el) => {
      length += readable(el).length;
      return length <= 300000;
    });
    if (!elements.length)
      throw Error(
        "Text blocks exceed the capture limit. Select or paste a shorter passage.",
      );
    const texts = elements.map(readable),
      source = location.href;
    artifact =
      restored?.artifact ?? (await makeArtifact(texts, source, document.title));
    if (!restored) {
      artifact.authors = pageCreators(document);
      const description = document.querySelector<HTMLMetaElement>('meta[name="description"],meta[property="og:description"]')?.content.trim();
      if (description) artifact.metaDescription = description.slice(0, 2000);
      artifact.capture = captureInfo;
      artifact.truncated = candidates.length > 1500 || length > 300000;
      let section = "";
      elements.forEach((el, i) => {
        const heading = /^H[1-6]$/.test(el.tagName)
          ? Number(el.tagName[1])
          : undefined;
        if (heading) section = readable(el).slice(0, 300);
        const ghost = el
          .closest('[class*="ghost-"]')
          ?.className.match(/(?:^|\s)ghost-(\d+)(?:\s|$)/)?.[1];
        const involvement = el.querySelector(".art-bright-span")
          ? "unknown"
          : ghost === "100"
            ? "original"
            : ghost === "95"
              ? "edited"
              : ghost === "60"
                ? "curated"
                : ghost === "0"
                  ? "ghost"
                  : undefined;
        artifact!.regions[i].pageHint = {
          ...(heading ? { heading } : {}),
          ...(section ? { section } : {}),
          ...(involvement ? { involvement } : {}),
        };
      });
    }
    if (
      source !== location.href ||
      elements.some((el, i) => !el.isConnected || readable(el) !== texts[i])
    )
      throw Error(
        "The page changed during capture. Capture again or paste an excerpt.",
      );
    index = new WeakMap();
    byId = new Map();
    elements.forEach((el, i) => {
      index.set(el, artifact!.regions[i].id);
      byId.set(artifact!.regions[i].id, el);
    });
    if (!restored)
      for (const [id, el] of byId) {
        const points = textPoints(el, excluded),
          emphasis: { start: number; end: number }[] = [],
          codeSpans: { start: number; end: number }[] = [];
        let lastParent: HTMLElement | null = null,
          bold = false;
        points.forEach((p, i) => {
          const parent = p.node.parentElement!;
          if (parent.closest("code,pre")) {
            const previous = codeSpans.at(-1);
            if (previous?.end === i) previous.end = i + 1;
            else codeSpans.push({ start: i, end: i + 1 });
          }
          if (parent !== lastParent) {
            bold = Number(getComputedStyle(parent).fontWeight) >= 600;
            lastParent = parent;
          }
          if (bold) {
            const previous = emphasis.at(-1);
            if (previous?.end === i) previous.end = i + 1;
            else emphasis.push({ start: i, end: i + 1 });
          }
        });
        if (emphasis.length)
          artifact!.regions.find((r) => r.id === id)!.emphasis = emphasis;
        if (codeSpans.length)
          artifact!.regions.find((r) => r.id === id)!.codeSpans = codeSpans;
      }
    for (const [i, el] of elements.entries()) {
      if (el.matches("footer"))
        artifact!.regions[i].pageHint = {
          ...artifact!.regions[i].pageHint,
          unit: "group",
          section: "References & Assets",
        };
    }
    reindex();
    observedRoot = root;
    themeChanged = false;
    observeSource();
    return artifact;
  };
  const target = (e: Event) => {
    let el = e.target as Element | null;
    while (el) {
      const id = index.get(el);
      if (id) return id;
      el = el.parentElement;
    }
    return null;
  };
  const offsetAt = (id: string, e: MouseEvent) => {
    const sentence = ranges
      .get(id)
      ?.find((s) =>
        Array.from(s.range.getClientRects()).some(
          (r) =>
            e.clientX >= r.left - 2 &&
            e.clientX <= r.right + 2 &&
            e.clientY >= r.top - 2 &&
            e.clientY <= r.bottom + 2,
        ),
      );
    if (!sentence) return;
    const caret = document.caretRangeFromPoint(e.clientX, e.clientY);
    const offsets = caret && pointOffsets.get(caret.startContainer);
    const offset =
      caret && offsets
        ? (offsets[caret.startOffset] ?? offsets[caret.startOffset - 1])
        : undefined;
    return Math.max(
      sentence.start,
      Math.min(offset ?? sentence.start, sentence.end - 1),
    );
  };
  document.addEventListener(
    "pointermove",
    (e) => {
      const id = target(e);
      if (!id) {
        if (selected && !pinned) leave();
        return;
      }
      const offset = offsetAt(id, e);
      if (
        offset !== undefined &&
        (id !== selected || offset !== selectedOffset)
      )
        select(id, false, true, offset);
    },
    { signal: abort.signal, passive: true },
  );
  document.addEventListener("pointerleave", leave, {
    signal: abort.signal,
    passive: true,
  });
  document.addEventListener(
    "click",
    (e) => {
      if (
        e.button !== 0 ||
        !!window.getSelection()?.toString() ||
        (e.target as Element).closest(
          "a,button,input,textarea,select,[contenteditable]",
        )
      )
        return;
      const id = target(e);
      if (id) select(id, true, true, offsetAt(id, e) ?? 0);
    },
    { signal: abort.signal, passive: true },
  );
  document.addEventListener(
    "keydown",
    (e) => {
      if (e.key === "Escape") release();
      const reading = (e.target as Element).closest<HTMLElement>(
        "[data-tompathy-reading]",
      );
      if (
        reading &&
        !reading.closest("a,button") &&
        (e.key === "Enter" || e.key === " ")
      ) {
        const id = target(e);
        if (id) {
          e.preventDefault();
          select(id, true, true, Number(reading.dataset.tompathyOffset));
        }
      }
    },
    { signal: abort.signal },
  );
  document.addEventListener("dblclick", () => release(), {
    signal: abort.signal,
    passive: true,
  });
  document.addEventListener(
    "focusin",
    (e) => {
      const reading = (e.target as Element).closest<HTMLElement>(
        "[data-tompathy-reading]",
      );
      const id = target(e);
      if (reading && id)
        select(id, false, true, Number(reading.dataset.tompathyOffset));
    },
    { signal: abort.signal },
  );
  document.addEventListener(
    "scroll",
    (e) => {
      if (
        pinned &&
        findAcknowledged &&
        !(e.target instanceof Element && e.target.closest("[data-tompathy-ui]"))
      ) {
        findAcknowledged = false;
        send("TOMPATHY_SCROLLED");
      }
    },
    { capture: true, passive: true, signal: abort.signal },
  );
  const listener = (
    m: any,
    _sender: chrome.runtime.MessageSender,
    respond: (r: any) => void,
  ) => {
    if (location.protocol === "chrome-extension:" && m.targetTabId !== ownTabId)
      return;
    if (m.type === "TOMPATHY_CAPTURE") {
      capture()
        .then((a) =>
          respond({
            artifact: a,
            restored,
            contextSources: restored ? [] : pageCreatorSources(document),
            repositoryLinks: restored ? [] : pageRepositoryLinks(document),
          }),
        )
        .catch((e) => respond({ error: e.message }));
      return true;
    }
    if (m.type === "TOMPATHY_CLEANUP") {
      window.__tompathyCleanup?.();
      respond({ ok: true });
      return;
    }
    if (
      !artifact ||
      m.documentId !== artifact.id ||
      m.revision !== artifact.revision ||
      stale
    )
      return;
    if (m.type === "TOMPATHY_OPEN_ESSAY") {
      void essay.open(m.kind, m.theme).then(ok => respond({ ok }));
      return true;
    }
    if (m.type === "TOMPATHY_MARK") {
      observer.disconnect();
      clear();
      if (m.ghostReadings?.length) {
        ensureFont();
        removeReading = annotatePage(
          byId,
          artifact,
          {
            ghostReadings: m.ghostReadings,
            evidence: m.evidence ?? [],
            origin: m.origin ?? "imported",
          },
          m.maker,
          excluded,
        );
      }
      reindex();
      observeSource();
      for (const e of (m.estimates ?? []) as Packet["estimates"]) {
        const el = elements.find((el) => index.get(el) === e.region);
        if (el) {
          originalTitles.set(el, el.getAttribute("title"));
          if (!m.ghostReadings?.length)
            el.title = contributionExplanation(
              {
                estimates: m.estimates,
                documentContribution: m.documentContribution,
              },
              e.region,
            );
          el.setAttribute("data-tompathy-mark", "");
          if (e.contribution != null)
            el.style.setProperty(
              "--tompathy-tint",
              String(e.contribution.value * 0.14),
            );
          el.setAttribute("data-tompathy-uncertain", e.uncertainty.level);
        }
      }
    }
    if (m.type === "TOMPATHY_FOCUS") {
      cancelFind();
      pinned = false;
      select(m.region, true, false, m.offset ?? 0);
      if (Array.isArray(m.regions))
        paint(
          "tompathy-active",
          m.regions.flatMap((id: string) =>
            (ranges.get(id) ?? []).map((s) => s.range),
          ),
        );
    }
    if (
      (m.type === "TOMPATHY_FIND" ||
        (m.type === "TOMPATHY_FOCUS" && m.center)) &&
      pinned &&
      m.region === selected
    ) {
      const selectedRanges = [
        ...(highlights?.get("tompathy-active") ?? []),
      ] as Range[];
      if (selectedRanges.length) {
        cancelFind();
        cancelFind = findSentence(
          selectedRanges,
          () => {
            findAcknowledged = true;
            send("TOMPATHY_FOUND");
          },
          () => {
            findAcknowledged = false;
            send("TOMPATHY_SCROLLED");
          },
        );
      }
    }
    if (m.type === "TOMPATHY_RELEASE") {
      cancelFind();
      release();
    }
    if (m.type === "TOMPATHY_LOCK_REMINDER") remind();
    if (m.type === "TOMPATHY_RELATED") {
      if (!pinned) {
        highlights?.delete("tompathy-active");
        byId.get(selected)?.removeAttribute("data-tompathy-selected");
        selected = "";
      }
      paint(
        "tompathy-related",
        m.span
          ? (ranges.get(m.span.region) ?? [])
              .filter((s) => s.start >= m.span.start && s.end <= m.span.end)
              .map((s) => s.range)
          : [],
      );
      elements.forEach((el) =>
        el.toggleAttribute(
          "data-tompathy-related",
          !m.span && (m.regions ?? []).includes(index.get(el)),
        ),
      );
    }
    respond({ ok: true });
  };
  chrome.runtime.onMessage.addListener(listener);
  window.__tompathyCleanup = () => {
    essay.close();
    cancelFind();
    abort.abort();
    observer.disconnect();
    clearTimeout(timer);
    clear();
    marker.remove();
    removeHelp();
    document.fonts.delete(font);
    chrome.runtime.onMessage.removeListener(listener);
    document.adoptedStyleSheets = document.adoptedStyleSheets.filter(
      (s) => s !== sheet,
    );
    delete window.__tompathyCleanup;
  };
  return { capture };
}
if (typeof chrome !== "undefined" && chrome.runtime?.id) {
  installPageAdapter();
  if (location.protocol === "chrome-extension:")
    void chrome.tabs.getCurrent().then((tab) => {
      chrome.runtime.onMessage.addListener((m, _sender, respond) => {
        if (
          m.type === "TOMPATHY_CAPTURE" &&
          m.targetTabId === tab?.id &&
          !window.__tompathyCleanup
        ) {
          installPageAdapter()
            .capture()
            .then((artifact) =>
              respond({
                artifact,
                restored: window.__tompathySnapshot,
                repositoryLinks: window.__tompathySnapshot
                  ? []
                  : pageRepositoryLinks(document),
                contextSources: window.__tompathySnapshot
                  ? []
                  : pageCreatorSources(document),
              }),
            )
            .catch((e) => respond({ error: e.message }));
          return true;
        }
      });
    });
}
