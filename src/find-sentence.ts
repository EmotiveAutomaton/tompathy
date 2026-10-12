/** Scroll the exact sentence into view, then briefly deepen its existing highlight.
 * A scroll-settled debounce also covers nested scroll containers and reduced motion. */
export function findSentence(range: Range, onFound: () => void) {
  const abort = new AbortController();
  const highlights = (CSS as any).highlights;
  const sheet = new CSSStyleSheet();
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
    abort.abort();
    highlights?.set("tompathy-found", new (window as any).Highlight(range));
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
  (range.startContainer instanceof Element
    ? range.startContainer
    : range.startContainer.parentElement
  )?.scrollIntoView({
    block: "center",
    inline: "nearest",
    behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "instant"
      : "smooth",
  });
  schedule();
  return cleanup;
}
