/** Center the highlighted text group, then briefly deepen its existing highlight.
 * A scroll-settled debounce also covers nested scroll containers and reduced motion. */
export function findSentence(
  input: Range | Range[],
  onFound: () => void,
  onAway: () => void = () => {},
) {
  const ranges = Array.isArray(input) ? input : [input];
  if (!ranges.length) return () => {};
  const abort = new AbortController();
  const highlights = (CSS as any).highlights;
  const sheet = new CSSStyleSheet();
  const destinations: { element: Element; top: number }[] = [];
  let windowTop = 0;
  sheet.replaceSync(
    "::highlight(tompathy-found){background-color:#56867466;color:inherit}",
  );
  document.adoptedStyleSheets = [...document.adoptedStyleSheets, sheet];
  let settle: ReturnType<typeof setTimeout>,
    pulse: ReturnType<typeof setTimeout>;
  const cleanup = () => {
    abort.abort();
    clearTimeout(settle);
    clearTimeout(pulse);
    highlights?.delete("tompathy-found");
    document.adoptedStyleSheets = document.adoptedStyleSheets.filter(
      (s) => s !== sheet,
    );
  };
  const finish = () => {
    if (
      Math.abs(scrollY - windowTop) > 3 ||
      destinations.some(
        ({ element, top }) => Math.abs(element.scrollTop - top) > 3,
      )
    ) {
      cleanup();
      onAway();
      return;
    }
    abort.abort();
    highlights?.set("tompathy-found", new (window as any).Highlight(...ranges));
    onFound();
    pulse = setTimeout(cleanup, 700);
  };
  const schedule = () => {
    clearTimeout(settle);
    settle = setTimeout(finish, 180);
  };
  document.addEventListener("scroll", schedule, {
    capture: true,
    passive: true,
    signal: abort.signal,
  });
  const rectangles = ranges
    .flatMap((r) => [...r.getClientRects()])
    .filter((r) => r.width && r.height);
  if (!rectangles.length) {
    cleanup();
    return () => {};
  }
  let center =
    (Math.min(...rectangles.map((r) => r.top)) +
      Math.max(...rectangles.map((r) => r.bottom))) /
    2;
  let ancestor: Node | null = ranges[0].commonAncestorContainer;
  while (
    ancestor &&
    !ranges.every((r) => ancestor!.contains(r.commonAncestorContainer))
  )
    ancestor = ancestor.parentNode;
  let el = ancestor instanceof HTMLElement ? ancestor : ancestor?.parentElement;
  const behavior = matchMedia("(prefers-reduced-motion: reduce)").matches
    ? "instant"
    : "smooth";
  for (
    ;
    el && el !== document.body && el !== document.documentElement;
    el = el.parentElement
  ) {
    if (
      !/(auto|scroll)/.test(getComputedStyle(el).overflowY) ||
      el.scrollHeight <= el.clientHeight
    )
      continue;
    const top = el.getBoundingClientRect().top + el.clientTop;
    const target = Math.max(
      0,
      Math.min(
        el.scrollHeight - el.clientHeight,
        el.scrollTop + center - top - el.clientHeight / 2,
      ),
    );
    center -= target - el.scrollTop;
    destinations.push({ element: el, top: target });
    el.scrollTo({ top: target, behavior });
  }
  windowTop = Math.max(
    0,
    Math.min(
      document.documentElement.scrollHeight - innerHeight,
      scrollY + center - innerHeight / 2,
    ),
  );
  window.scrollBy({ top: center - innerHeight / 2, behavior });
  schedule();
  return cleanup;
}
