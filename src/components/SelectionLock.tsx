import { LOCK_PATH } from "../core/lock";
export function SelectionLock({
  onUnlock,
  className = "",
}: {
  onUnlock: () => void;
  className?: string;
}) {
  return (
    <button
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
