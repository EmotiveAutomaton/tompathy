import { ghostInk, grade, type ReadingHelp } from "./core/ghost";
/** A single delegated, dismissible card shared by the preview and page adapter. */
export const readingCSS = `
.tompathy-ghost{font-family:"ToMpathy Reading",Georgia,serif!important;font-weight:400!important;font-synthesis:none;box-decoration-break:clone;-webkit-box-decoration-break:clone;border-radius:3px}
.tompathy-emphasis{text-decoration-line:underline!important;text-decoration-thickness:1px;text-underline-offset:.17em}
.tompathy-reading-help{all:initial;box-sizing:border-box;position:fixed;z-index:2147483646;width:min(410px,calc(100vw - 24px));padding:17px 19px;background:#f8faf5;color:#273e39;border:1px solid #b9cabc;border-radius:12px;box-shadow:0 8px 30px #183c2926;font:12px/1.6 system-ui,sans-serif;overflow:auto;max-height:calc(100vh - 24px)}
 .tompathy-reading-help[hidden]{display:none}
`;
const detailCSS = `
.reading-summary{display:grid;grid-template-columns:78px minmax(0,1fr);gap:16px;align-items:center;margin:0 0 14px;position:relative}
.reading-sample{display:grid;place-items:center;min-height:108px;font:42px/1 "ToMpathy Reading",Georgia,serif}
.reading-sample span{padding:3px;border-radius:5px}
.reading-leaders{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible}
.reading-scales{min-width:0}
.reading-axis{position:relative;margin:0 0 12px;padding-top:2px}
.reading-axis:last-child{margin-bottom:0}
.reading-scale{position:relative;display:block;width:100%;box-sizing:border-box;text-align:right;white-space:nowrap;padding:9px 0 0;font:10px/1.5 "ToMpathy Reading",Georgia,serif}
.reading-scale span{padding:1px 0}
.reading-value{display:block;width:fit-content;margin:0 0 3px auto;border-radius:3px;font:13px/1.5 "ToMpathy Reading",Georgia,serif}
ul{margin:0;padding-left:16px;border-top:1px solid #d6dfd4;padding-top:4px}li{font:12px/1.55 system-ui;margin:9px 0 0;padding-left:2px}
.reading-prompt{margin-top:12px;padding-top:9px;border-top:1px solid #d6dfd4}.reading-prompt strong{font:600 11px/1.5 system-ui}.reading-prompt blockquote{margin:4px 0 0;font:12px/1.55 Georgia,serif}
@media (max-width:360px){.reading-summary{grid-template-columns:56px minmax(0,1fr);gap:12px}.reading-sample{font-size:34px}.reading-scale{font-size:9px}}
`;
const privateHelp = new WeakMap<HTMLElement, ReadingHelp>();
export function registerReadingHelp(element: HTMLElement, help: ReadingHelp) {
  privateHelp.set(element, help);
}
export function attachReadingHelp(root: Document = document, isolated = false) {
  const abort = new AbortController(),
    sheet = new CSSStyleSheet();
  sheet.replaceSync(readingCSS);
  root.adoptedStyleSheets = [...root.adoptedStyleSheets, sheet];
  const card = root.createElement("div");
  card.className = "tompathy-reading-help";
  card.id = "tompathy-sentence-help";
  card.setAttribute("role", "tooltip");
  card.setAttribute("data-tompathy-ui", "");
  card.hidden = true;
  const content = isolated ? card.attachShadow({ mode: "closed" }) : card;
  if (content instanceof ShadowRoot) {
    const details = new CSSStyleSheet();
    details.replaceSync(detailCSS);
    content.adoptedStyleSheets = [details];
  } else {
    const scoped = detailCSS.replace(
      /(^|})\s*([^@{}][^{}]*)\{/g,
      (_, prefix, selector) =>
        `${prefix}${selector
          .split(",")
          .map((part: string) => ".tompathy-reading-help " + part.trim())
          .join(",")} {`,
    );
    sheet.replaceSync(readingCSS + scoped);
  }
  root.documentElement.append(card);
  let owner: HTMLElement | null = null,
    timer: ReturnType<typeof setTimeout> | undefined;
  let keyboardOwner = false;
  let x = 0,
    y = 0;
  const hide = () => {
    clearTimeout(timer);
    card.hidden = true;
    owner?.removeAttribute("aria-describedby");
    owner = null;
  };
  const show = () => {
    if (!owner?.isConnected) return hide();
    let help: ReadingHelp;
    try {
      help =
        privateHelp.get(owner) ??
        (isolated ? null : JSON.parse(owner.dataset.tompathyHelp!));
      if (!help || !help.label) return hide();
    } catch {
      return hide();
    }
    const el = (tag: string, text = "", className = "") => {
      const item = root.createElement(tag);
      item.textContent = text;
      item.className = className;
      return item;
    };
    const summary = el("div", "", "reading-summary"),
      sample = el("div", "", "reading-sample"),
      letters = el("span", "Aa"),
      labels = el("div", "", "reading-scales");
    sample.setAttribute("aria-hidden", "true");
    const paint = (target: HTMLElement, kind: ReadingHelp["kind"]) => {
      const ink = ghostInk(kind, [38, 58, 50], [248, 250, 245]);
      target.style.color = ink.color;
      target.style.background = ink.background;
    };
    paint(letters, help.kind);
    letters.style.fontVariationSettings = `"GRAD" ${grade(help.confidence)}`;
    sample.append(letters);
    const axis = (text: string, confidence: boolean) => {
      const row = el("div", "", "reading-axis"),
        scale = el("span", "", "reading-scale");
      scale.setAttribute("aria-label", text);
      scale.setAttribute("role", "img");
      const count = text.length;
      for (let i = 0; i < count; i++) {
        const part = el(
          "span",
          text.slice(
            Math.round((i * text.length) / count),
            Math.round(((i + 1) * text.length) / count),
          ),
        );
        part.setAttribute("aria-hidden", "true");
        if (confidence) {
          const t = i / (count - 1);
          part.style.fontVariationSettings = `"GRAD" ${Math.round(-50 + 150 * t)}`;
          part.style.opacity = String(0.24 + 0.76 * t);
          part.style.webkitTextStrokeWidth = `${Math.max(0, t - 0.2) * 1.05}px`;
        } else {
          const t = i / (count - 1);
          // Fade the reversed swatch into curator ink, then steadily darken.
          // This is a visual legend; it does not alter the supplied categories.
          const reverse = Math.max(0, 1 - t / 0.3);
          const ink = 0.56 + 0.44 * Math.max(0, (t - 0.3) / 0.7);
          const normal = [38, 58, 50].map((v, j) =>
            Math.round(v * ink + [248, 250, 245][j] * (1 - ink)),
          );
          part.style.color = `rgb(${normal.map((v, j) => Math.round(v * (1 - reverse) + [248, 250, 245][j] * reverse)).join(",")})`;
          part.style.backgroundColor = `rgba(38,58,50,${reverse})`;
        }
        scale.append(part);
      }
      const value = el(
        "span",
        confidence
          ? help.confidence === null
            ? "Not supplied"
            : `${Math.round(help.confidence * 100)}%`
          : help.label,
        "reading-value",
      );
      if (confidence)
        value.style.fontVariationSettings = `"GRAD" ${Math.max(0, grade(help.confidence))}`;
      else paint(value, help.kind);
      row.append(value, scale);
      return row;
    };
    labels.append(
      axis("Less · creator involvement · More", false),
      axis("Less · confidence · More", true),
    );
    summary.append(sample, labels);
    const list = el("ul");
    for (const evidence of help.evidence.slice(0, 3))
      list.append(el("li", evidence.text));
    content.replaceChildren(summary, ...(help.evidence.length ? [list] : []));
    if (help.kind === "ghost" && help.prompt) {
      const prompt = el("div", "", "reading-prompt");
      prompt.append(
        el("strong", "Estimated generation prompt"),
        el("blockquote", help.prompt),
      );
      content.append(prompt);
    }
    card.hidden = false;
    // Fine callout lines join the two scales directly to the sample's ink.
    const ns = "http://www.w3.org/2000/svg",
      leaders = root.createElementNS(ns, "svg");
    leaders.setAttribute("class", "reading-leaders");
    leaders.setAttribute("aria-hidden", "true");
    const origin = summary.getBoundingClientRect(),
      letterBox = letters.getBoundingClientRect();
    labels.querySelectorAll(".reading-scale").forEach((scale, i) => {
      const b = scale.getBoundingClientRect(),
        line = root.createElementNS(ns, "path");
      const x = letterBox.right - origin.left - 4,
        y = letterBox.top - origin.top + letterBox.height * (i ? 0.66 : 0.4);
      const endX = b.left - origin.left - 1,
        endY = b.top - origin.top + 3;
      line.setAttribute(
        "d",
        `M${x},${y} C${x + 9},${y} ${endX - 26},${endY} ${endX},${endY}`,
      );
      line.setAttribute("fill", "none");
      line.setAttribute("stroke", "#82958a");
      line.setAttribute("stroke-width", "1");
      leaders.append(line);
      const arrow = root.createElementNS(ns, "path");
      const tip = b.right - origin.left;
      arrow.setAttribute(
        "d",
        `M${endX},${endY - 0.3} L${tip - 6},${endY - 1.9} L${tip - 6},${endY - 4.5} L${tip},${endY} L${tip - 6},${endY + 4.5} L${tip - 6},${endY + 1.9} L${endX},${endY + 0.3} Z`,
      );
      arrow.setAttribute("fill", "#82958a");
      leaders.append(arrow);
    });
    summary.append(leaders);
    owner.setAttribute("aria-describedby", card.id);
    const r = card.getBoundingClientRect();
    card.style.left = `${Math.max(12, Math.min(innerWidth - r.width - 12, x))}px`;
    card.style.top = `${Math.max(12, y + 18 + r.height < innerHeight - 12 ? y + 18 : y - r.height - 12)}px`;
  };
  const enterTarget = (
    target: Element,
    focused: boolean,
    point?: { x: number; y: number },
  ) => {
    if (card.contains(target)) {
      clearTimeout(timer);
      return;
    }
    const next =
      target.closest<HTMLElement>(
        "[data-tompathy-help],[data-tompathy-reading]",
      ) ??
      (focused
        ? target.querySelector<HTMLElement>(
            "[data-tompathy-help],[data-tompathy-reading]",
          )
        : null);
    if (next === owner) return;
    hide();
    if (!next) return;
    owner = next;
    keyboardOwner = focused;
    const r = next.getBoundingClientRect();
    x = point?.x ?? r.left;
    y = point?.y ?? r.bottom;
    timer = setTimeout(show, focused ? 0 : 650);
  };
  const enter = (event: Event) =>
    enterTarget(
      event.target as Element,
      event.type === "focusin",
      event instanceof PointerEvent
        ? { x: event.clientX, y: event.clientY }
        : undefined,
    );
  root.addEventListener("pointerover", enter, { signal: abort.signal });
  root.addEventListener("focusin", enter, { signal: abort.signal });
  root.addEventListener(
    "pointerout",
    (e) => {
      const next = e.relatedTarget as Node | null;
      if (next && (owner?.contains(next) || card.contains(next))) return;
      clearTimeout(timer);
      timer = setTimeout(hide, 120);
    },
    { signal: abort.signal },
  );
  root.addEventListener("focusout", hide, { signal: abort.signal });
  root.addEventListener(
    "keydown",
    (e) => {
      if (e.key === "Escape") hide();
    },
    { signal: abort.signal },
  );
  root.addEventListener(
    "scroll",
    (e) => {
      if (!card.contains(e.target as Node)) {
        const focused = keyboardOwner ? root.activeElement : null;
        hide();
        // A scroll can finish after pointerover (including browser auto-scroll).
        // Re-test the actual point once settled, so the tooltip does not require
        // leaving and re-entering the sentence just to become discoverable.
        timer = setTimeout(() => {
          if (
            focused &&
            focused === root.activeElement &&
            focused !== root.body
          ) {
            enterTarget(focused, true);
            return;
          }
          const target = root.elementFromPoint(x, y);
          if (target) enterTarget(target, false, { x, y });
        }, 180);
      }
    },
    { capture: true, passive: true, signal: abort.signal },
  );
  return () => {
    hide();
    abort.abort();
    card.remove();
    root.adoptedStyleSheets = root.adoptedStyleSheets.filter(
      (s) => s !== sheet,
    );
  };
}
