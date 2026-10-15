import type { Artifact, Packet } from "./core/model";
import { ghostAt, ghostInk, grade, readingHelp, rgb } from "./core/ghost";
import { regionSentences } from "./core/sentences";
import { registerReadingHelp } from "./reading-help";

export function textPoints(el: HTMLElement, excluded: string) {
  const points: { node: Text; offset: number }[] = [],
    walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  let node: Node | null,
    pending: { node: Text; offset: number } | null = null;
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
        if (points.length) pending = { node: node as Text, offset };
      } else {
        if (pending) {
          points.push(pending);
          pending = null;
        }
        points.push({ node: node as Text, offset });
      }
    }
  }
  return points;
}
function surface(el: HTMLElement) {
  for (let p: HTMLElement | null = el; p; p = p.parentElement) {
    const c = getComputedStyle(p).backgroundColor,
      values = c.match(/[\d.]+/g)?.map(Number);
    if (values && (values.length === 3 || values[3] === 1)) return rgb(c);
  }
  return [255, 255, 255] as [number, number, number];
}
/** Splits text nodes only. Existing elements, links and their listeners survive. */
export function annotatePage(
  elements: Map<string, HTMLElement>,
  artifact: Artifact,
  packet: Pick<Packet, "ghostReadings" | "evidence" | "origin">,
  maker: string,
  excluded: string,
) {
  const restores: (() => void)[] = [];
  const opacityCandidates = new Set<HTMLElement>();
  for (const r of artifact.regions) {
    const el = elements.get(r.id);
    if (!el) continue;
    const points = textPoints(el, excluded),
      regions = regionSentences(r);
    const byNode = new Map<Text, { offset: number; index: number }[]>();
    points.forEach((p, index) => {
      const entries = byNode.get(p.node) ?? [];
      entries.push({ offset: p.offset, index });
      byNode.set(p.node, entries);
    });
    for (const [node, entries] of byNode) {
      const parent = node.parentElement;
      if (!parent) continue;
      const raw = node.data,
        computed = getComputedStyle(parent),
        background = surface(parent),
        foreground = rgb(computed.color);
      const runs = regions.flatMap((s) => {
        const included = entries.filter(
          (e) => e.index >= s.start && e.index < s.end,
        );
        if (!included.length) return [];
        return [
          {
            sentenceStart: s.start,
            begins: included[0].index === s.start,
            start: included[0].offset,
            end: included[included.length - 1].offset + 1,
            reading: ghostAt(packet as Packet, maker, r.id, s.start, s.end),
          },
        ];
      });
      const fragment = document.createDocumentFragment(),
        pieces: Node[] = [];
      let cursor = 0;
      const add = (n: Node) => {
        pieces.push(n);
        fragment.append(n);
      };
      for (const run of runs) {
        if (run.start > cursor)
          add(document.createTextNode(raw.slice(cursor, run.start)));
        const span = document.createElement("span"),
          reading = run.reading;
        span.dataset.tompathyReading = "";
        span.dataset.tompathyOffset = String(run.sentenceStart);
        if (run.begins && !parent.closest("a,button")) span.tabIndex = 0;
        registerReadingHelp(span, readingHelp(reading, packet));
        span.textContent = raw.slice(run.start, run.end);
        if (reading && reading.kind !== "unknown") {
          for (
            let ancestor: HTMLElement | null = parent;
            ancestor && ancestor !== document.body;
            ancestor = ancestor.parentElement
          )
            opacityCandidates.add(ancestor);
          const ink = ghostInk(reading.kind, foreground, background);
          span.className =
            "tompathy-ghost" +
            (Number(computed.fontWeight) >= 600 ? " tompathy-emphasis" : "");
          span.dataset.ghostKind = reading.kind;
          span.style.setProperty("color", ink.color, "important");
          span.style.setProperty("opacity", "1", "important");
          span.style.setProperty(
            "background-color",
            ink.background,
            "important",
          );
          span.style.setProperty(
            "font-variation-settings",
            `"GRAD" ${grade(reading.confidence)}`,
            "important",
          );
          // Establish the measured surface on pages with images or translucent layers.
          if (reading.kind !== "ghost")
            span.style.setProperty(
              "background-color",
              `rgb(${background.join(",")})`,
              "important",
            );
        }
        add(span);
        cursor = run.end;
      }
      if (cursor < raw.length) add(document.createTextNode(raw.slice(cursor)));
      node.replaceWith(fragment);
      restores.push(() => {
        if (
          pieces.every((n) => n.parentNode === parent) &&
          pieces.map((n) => n.textContent).join("") === raw
        ) {
          if (pieces[0]) parent.replaceChild(node, pieces[0]);
          pieces.slice(1).forEach((n) => n.parentNode?.removeChild(n));
        } else
          for (const p of pieces)
            if (
              p instanceof HTMLElement &&
              p.dataset.tompathyReading !== undefined
            )
              p.replaceWith(...p.childNodes);
      });
    }
  }
  // Opacity on an ancestor multiplies every descendant: child opacity cannot
  // undo it. Reset only text-only subtrees wholly covered by our treatment.
  // Unrelated text, images, controls and page-level overlays retain their styles.
  for (const ancestor of opacityCandidates) {
    if (
      Number(getComputedStyle(ancestor).opacity) >= 1 ||
      ancestor.matches(excluded) ||
      ancestor.querySelector(
        `img,svg,video,canvas,iframe,input,button,select,textarea,${excluded}`,
      )
    )
      continue;
    const walker = document.createTreeWalker(ancestor, NodeFilter.SHOW_TEXT);
    let node: Node | null,
      covered = true;
    while ((node = walker.nextNode())) {
      if (
        node.textContent?.trim() &&
        !node.parentElement?.closest(".tompathy-ghost")
      ) {
        covered = false;
        break;
      }
    }
    if (!covered) continue;
    const value = ancestor.style.getPropertyValue("opacity"),
      priority = ancestor.style.getPropertyPriority("opacity"),
      hadStyle = ancestor.hasAttribute("style");
    ancestor.style.setProperty("opacity", "1", "important");
    restores.push(() => {
      // A site's subsequent edit owns the property; do not overwrite it.
      if (
        ancestor.style.getPropertyValue("opacity") !== "1" ||
        ancestor.style.getPropertyPriority("opacity") !== "important"
      )
        return;
      if (value) ancestor.style.setProperty("opacity", value, priority);
      else ancestor.style.removeProperty("opacity");
      if (!hadStyle && !ancestor.style.length)
        ancestor.removeAttribute("style");
    });
  }
  return () => {
    restores.forEach((restore) => restore());
  };
}
