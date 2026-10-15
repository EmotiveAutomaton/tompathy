import { useEffect, useRef } from "react";
import { LOCK_PATH, pulseLock } from "../core/lock";
export function SelectionLock({
  onUnlock,
  className = "",
  reminder = 0,
}: {
  onUnlock: () => void;
  className?: string;
  reminder?: number;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (reminder && ref.current) return pulseLock(ref.current);
  }, [reminder]);
  return (
    <button
      ref={ref}
      type="button"
      className={`selection-lock ${className}`}
      aria-label="Unlock selection"
      title="Unlock selection · Escape"
      onClick={(e) => {
        e.stopPropagation();
        onUnlock();
      }}
    >
      <svg
        width="13"
        height="13"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d={LOCK_PATH} />
      </svg>
    </button>
  );
}
