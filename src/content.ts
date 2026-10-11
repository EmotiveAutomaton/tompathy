import { makeArtifact, normalize } from "./core/artifact";
import type { Artifact, Packet } from "./core/model";
import { pageAuthors, readingRoot } from "./core/page";
import { contributionExplanation } from "./core/reading";
declare global {
  interface Window {
    __tompathyCleanup?: () => void;
  }
}
export function installPageAdapter() {
  window.__tompathyCleanup?.();
  let artifact: Artifact | null = null,
    elements: HTMLElement[] = [],
    index = new WeakMap<Element, string>(),
    byId = new Map<string, HTMLElement>(),
    pinned = false,
    selected = "",
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
  sheet.replaceSync(
    '[data-tompathy-mark]{background-color:rgba(192,133,40,var(--tompathy-tint,0)) !important;border-radius:3px}[data-tompathy-uncertain="high"]{text-decoration:underline dotted #9c793e !important;text-underline-offset:5px}[data-tompathy-selected]{outline:2px solid #b77c20 !important;outline-offset:5px}[data-tompathy-related]{outline:1px dashed #557a70 !important;outline-offset:4px}',
  );
  document.adoptedStyleSheets = [...document.adoptedStyleSheets, sheet];
  const clear = () =>
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
  const select = (id: string, pin = false, notify = true) => {
    if (stale || (!pin && pinned)) return;
    byId.get(selected)?.removeAttribute("data-tompathy-selected");
    selected = id;
    if (pin) pinned = true;
    byId.get(id)?.setAttribute("data-tompathy-selected", "");
    if (notify) send("TOMPATHY_SELECT", { region: id, pinned });
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
    observer.disconnect();
    clear();
    pinned = false;
    selected = "";
    stale = false;
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
    artifact = await makeArtifact(texts, source, document.title);
    artifact.authors = pageAuthors(document);
    artifact.capture = captureInfo;
    artifact.truncated = candidates.length > 1500 || length > 300000;
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
  document.addEventListener(
    "pointerover",
    (e) => {
      const id = target(e);
      if (id && id !== selected) select(id);
    },
    { signal: abort.signal, passive: true },
  );
  document.addEventListener(
    "click",
    (e) => {
      if (
        (e.target as Element).closest(
          "a,button,input,textarea,select,[contenteditable]",
        ) ||
        window.getSelection()?.toString()
      )
        return;
      const id = target(e);
      if (id) select(id, true);
    },
    { signal: abort.signal, passive: true },
  );
  document.addEventListener(
    "selectionchange",
    () => {
      const s = window.getSelection();
      if (!s || s.isCollapsed || s.toString().length < 12) return;
      let el = s.anchorNode?.parentElement;
      while (el) {
        const id = index.get(el);
        if (id) {
          select(id, true);
          return;
        }
        el = el.parentElement;
      }
    },
    { signal: abort.signal },
  );
  document.addEventListener(
    "keydown",
    (e) => {
      if (e.key === "Escape") {
        pinned = false;
        send("TOMPATHY_SELECT", { region: selected, pinned: false });
      }
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
        .then((a) => respond({ artifact: a }))
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
      select(m.region, true, false);
      elements
        .find((el) => index.get(el) === m.region)
        ?.scrollIntoView({
          block: "center",
          behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
            ? "instant"
            : "smooth",
        });
    }
    if (m.type === "TOMPATHY_RELEASE") pinned = false;
    if (m.type === "TOMPATHY_RELATED")
      elements.forEach((el) =>
        el.toggleAttribute(
          "data-tompathy-related",
          (m.regions ?? []).includes(index.get(el)),
        ),
      );
    respond({ ok: true });
  };
  chrome.runtime.onMessage.addListener(listener);
  window.__tompathyCleanup = () => {
    abort.abort();
    observer.disconnect();
    clearTimeout(timer);
    clear();
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
            .then((artifact) => respond({ artifact }))
            .catch((e) => respond({ error: e.message }));
          return true;
        }
      });
    });
}
