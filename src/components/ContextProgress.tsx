import { Check, CircleAlert } from "lucide-react";
export type ContextWork = {
  phase: "working" | "done" | "error";
  completed: number;
  total: number;
  label: string;
};
export function ContextProgress({ work }: { work: ContextWork | null }) {
  if (!work) return null;
  return (
    <span
      className={`context-progress ${work.phase}`}
      role="status"
      aria-label={work.label}
      title={work.label}
    >
      <span className="context-progress-label">
        {work.phase === "done"
          ? "Context ready"
          : work.phase === "error"
            ? "Check context"
            : work.label.startsWith("Read ")
              ? "Reading context"
              : work.label}
      </span>
      {work.phase === "error" ? (
        <CircleAlert size={16} />
      ) : (
        <span className="context-progress-mark">
          <svg
            className="context-progress-bar"
            role="progressbar"
            aria-label="Collecting creator context"
            aria-valuemin={0}
            aria-valuemax={work.total}
            aria-valuenow={work.completed}
            viewBox="0 0 34 12"
          >
            <rect
              x="1"
              y="2"
              width="32"
              height="8"
              rx="3"
              fill="none"
              stroke="currentColor"
              opacity=".4"
            />
            <rect
              className="context-progress-fill"
              x="3"
              y="4"
              width={
                work.phase === "done"
                  ? 28
                  : 28 * Math.min(1, work.completed / Math.max(1, work.total))
              }
              height="4"
              rx="2"
              fill="currentColor"
            />
          </svg>
          {work.phase === "done" && (
            <Check className="context-progress-check" size={16} />
          )}
        </span>
      )}
    </span>
  );
}
