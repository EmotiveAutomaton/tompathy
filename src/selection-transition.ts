/** A short, non-layout highlight bloom. No text, inference data or idle loop. */
export function selectionTransition() {
  let key = "",
    cancel = () => {};
  return {
    show(range: Range, next: string) {
      if (key === next) return;
      key = next;
      cancel();
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const host = document.createElement("div");
      host.dataset.tompathyUi = "";
      host.setAttribute("aria-hidden", "true");
      host.style.cssText =
        "all:initial;position:fixed;inset:0;pointer-events:none;z-index:2147483644";
      const shadow = host.attachShadow({ mode: "closed" });
      const animations: Animation[] = [];
      for (const r of Array.from(range.getClientRects()).slice(0, 24)) {
        if (!r.width || !r.height || r.bottom < 0 || r.top > innerHeight)
          continue;
        const mark = document.createElement("div");
        mark.style.cssText = `position:absolute;left:${r.left}px;top:${r.top}px;width:${r.width}px;height:${r.height}px;border-radius:3px;background:#56867428;pointer-events:none`;
        shadow.append(mark);
        animations.push(
          mark.animate(
            [
              { opacity: 0, transform: "scale(.995,.94)" },
              { opacity: 1, transform: "scale(1.003,1.04)", offset: 0.38 },
              { opacity: 0, transform: "scale(1)" },
            ],
            { duration: 230, easing: "ease-out" },
          ),
        );
      }
      document.documentElement.append(host);
      const remove = () => {
        host.remove();
        animations.forEach((a) => a.cancel());
      };
      const timer = setTimeout(remove, 250);
      cancel = () => {
        clearTimeout(timer);
        remove();
      };
    },
    clear() {
      cancel();
      key = "";
    },
  };
}
