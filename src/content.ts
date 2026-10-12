import { LOCK_SVG, LOCK_INK, LOCK_BACKGROUND } from "./core/lock";
import { sentences } from "./core/sentences";
import { makeArtifact, normalize } from "./core/artifact";
import {
  SessionSchema,
  type Artifact,
  type Packet,
  type Session,
} from "./core/model";
import { pageAuthors, pageAuthorSources, readingRoot } from "./core/page";
import { contributionExplanation } from "./core/reading";
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
  let ownTabId: number | undefined;
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
  marker.type = "button";
  marker.setAttribute("data-tompathy-ui", "");
  marker.setAttribute("aria-label", "Unlock selection");
  marker.title = "Unlock selection · Escape";
  marker.innerHTML = LOCK_SVG;
  marker.style.cssText = `all:initial;box-sizing:border-box;position:fixed;z-index:2147483647;cursor:pointer;width:23px;height:23px;align-items:center;justify-content:center;color:${LOCK_INK};background:${LOCK_BACKGROUND};border:1px solid #91b7a4;border-radius:50%;padding:0;box-shadow:0 1px 5px #426f5d22;display:none`;
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
      marker.style.left = `${Math.min(innerWidth - 24, r.right - 5)}px`;
      marker.style.top = `${r.bottom - 5}px`;
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
    'nav,header,footer,aside,button,input,textarea,select,[contenteditable]:not([contenteditable="false"]),[hidden],[aria-hidden="true"],[data-tompathy-ui],.entryFooter,.entry-footer,.post-footer,.related,.related-posts,.recent-articles,.subscription,.newsletter,.comments,#comments';
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
    readable(el).length >= 12;
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
  const release = () => {
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
    if (stale || (!pin && pinned)) return;
    byId.get(selected)?.removeAttribute("data-tompathy-selected");
    selected = id;
    const sentence =
      ranges.get(id)?.find((s) => s.start <= offset && s.end > offset) ??
      ranges.get(id)?.[0];
    selectedOffset = sentence
      ? Math.max(sentence.start, Math.min(offset, sentence.end - 1))
      : 0;
    if (pin) pinned = true;
    byId.get(id)?.setAttribute("data-tompathy-selected", "");
    paint("tompathy-active", sentence ? [sentence.range] : []);
    highlights?.delete("tompathy-related");
    elements.forEach((el) => el.removeAttribute("data-tompathy-related"));
    positionMarker();
    if (notify)
      send("TOMPATHY_SELECT", { region: id, offset: selectedOffset, pinned });
  };
  const leave = () => {
    if (!pinned) {
      highlights?.delete("tompathy-active");
      byId.get(selected)?.removeAttribute("data-tompathy-selected");
      selected = "";
    }
    send("TOMPATHY_LEAVE");
  };
  const observer = new MutationObserver((records) => {
    if (!artifact || stale || !records.length) return;
    clearTimeout(timer);
    timer = setTimeout(() => {
      stale = true;
      clear();
      send("TOMPATHY_STALE");
    }, 200);
  });
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
    const { root, capture: captureInfo } = readingRoot(document);
    const candidates = Array.from(
      root.querySelectorAll<HTMLElement>(
        "h1,h2,h3,h4,p,li,blockquote,pre,dd,dt,td",
      ),
    ).filter(eligible);
    const candidateSet = new Set(candidates);
    elements = candidates
      .filter(
        (el) =>
          !Array.from(
            el.querySelectorAll("h1,h2,h3,h4,p,li,blockquote,pre,dd,dt,td"),
          ).some((other) => candidateSet.has(other as HTMLElement)),
      )
      .slice(0, 1500);
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
      artifact.authors = pageAuthors(document);
      artifact.capture = captureInfo;
      artifact.truncated = candidates.length > 1500 || length > 300000;
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
    ranges.clear();
    pointOffsets = new WeakMap();
    elements.forEach((el, i) => {
      index.set(el, artifact!.regions[i].id);
      const id = artifact!.regions[i].id;
      byId.set(id, el);
      // Map normalized UTF-16 offsets back to original text nodes without wrapping or rewriting the page.
      const points: { node: Node; offset: number }[] = [];
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      let node: Node | null,
        pendingSpace: { node: Node; offset: number } | null = null;
      while ((node = walker.nextNode())) {
        if (
          !node.parentElement ||
          node.parentElement.closest(excluded) ||
          !node.parentElement.checkVisibility({ checkVisibilityCSS: true })
        )
          continue;
        const raw = node.textContent ?? "";
        for (let offset = 0; offset < raw.length; offset++) {
          if (/\s/u.test(raw[offset])) {
            if (points.length) pendingSpace = { node, offset };
          } else {
            if (pendingSpace) {
              points.push(pendingSpace);
              pendingSpace = null;
            }
            points.push({ node, offset });
          }
        }
      }
      for (let i = 0; i < points.length; i++) {
        const point = points[i],
          offsets = pointOffsets.get(point.node) ?? [];
        offsets[point.offset] = i;
        pointOffsets.set(point.node, offsets);
      }
      ranges.set(
        id,
        sentences(texts[i]).map((s) => {
          const range = document.createRange(),
            start = points[s.start],
            end = points[s.end - 1];
          range.setStart(start.node, start.offset);
          range.setEnd(end.node, end.offset + 1);
          return { start: s.start, end: s.end, range };
        }),
      );
    });
    observer.observe(root, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: ["hidden", "aria-hidden", "class"],
    });
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
    },
    { signal: abort.signal },
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
            contextSources: restored ? [] : pageAuthorSources(document),
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
    if (m.type === "TOMPATHY_MARK") {
      clear();
      for (const e of (m.estimates ?? []) as Packet["estimates"]) {
        const el = elements.find((el) => index.get(el) === e.region);
        if (el) {
          originalTitles.set(el, el.getAttribute("title"));
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
      pinned = false;
      select(m.region, true, false, m.offset ?? 0);
      if (Array.isArray(m.regions))
        paint(
          "tompathy-active",
          m.regions.flatMap((id: string) =>
            (ranges.get(id) ?? []).map((s) => s.range),
          ),
        );
      elements
        .find((el) => index.get(el) === m.region)
        ?.scrollIntoView({
          block: "center",
          behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
            ? "instant"
            : "smooth",
        });
    }
    if (m.type === "TOMPATHY_RELEASE") release();
    if (m.type === "TOMPATHY_RELATED") {
      if (!pinned) highlights?.delete("tompathy-active");
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
    abort.abort();
    observer.disconnect();
    clearTimeout(timer);
    clear();
    marker.remove();
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
                contextSources: window.__tompathySnapshot
                  ? []
                  : pageAuthorSources(document),
              }),
            )
            .catch((e) => respond({ error: e.message }));
          return true;
        }
      });
    });
}
