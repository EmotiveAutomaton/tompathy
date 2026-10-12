/** Shared vector and colors for the page marker and the panel control. */
export const LOCK_PATH =
  "M7 11V7a5 5 0 0 1 10 0v4M6 11h12a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2ZM12 15v3";
export const LOCK_INK = "#426f5d";
export const LOCK_BACKGROUND = "#edf3ec";
/** Local interaction hint only: no cursor history or telemetry is persisted. */
export function blockedFocusTracker() {
  let previous = "",
    times: number[] = [],
    lastPulse = -Infinity;
  return {
    reset() {
      previous = "";
      times = [];
      lastPulse = -Infinity;
    },
    acknowledge(now: number) {
      times = [];
      lastPulse = now;
    },
    attempt(key: string, now: number) {
      if (key === previous) return false;
      previous = key;
      if (now - lastPulse < 6000) return false;
      if (times.length && now - times[times.length - 1] < 40) return false;
      times = times.filter((t) => now - t < 1200);
      times.push(now);
      if (times.length < 4) return false;
      times = [];
      lastPulse = now;
      return true;
    },
  };
}
export function pulseLock(element: HTMLElement) {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const glow = "0 0 0 4px #56867466, 0 0 12px #56867444";
  const resting = getComputedStyle(element).boxShadow;
  element.dataset.lockReminder = "active";
  const animation = element.animate(
    reduced
      ? [{ boxShadow: glow }, { boxShadow: glow }]
      : [
          { boxShadow: resting },
          { boxShadow: glow, offset: 0.5 },
          { boxShadow: resting },
        ],
    { duration: reduced ? 1100 : 650, iterations: reduced ? 1 : 2 },
  );
  animation.id = "tompathy-lock-reminder";
  const cleanup = () => {
    delete element.dataset.lockReminder;
    animation.cancel();
  };
  animation.onfinish = cleanup;
  return cleanup;
}
export const LOCK_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="${LOCK_INK}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${LOCK_PATH}"/></svg>`;
