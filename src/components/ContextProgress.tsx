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
      {work.phase === "done" ? (
        <Check size={16} />
      ) : work.phase === "error" ? (
        <CircleAlert size={16} />
      ) : (
        <svg
          role="progressbar"
          aria-label="Collecting author context"
          aria-valuemin={0}
          aria-valuemax={work.total}
          aria-valuenow={work.completed}
          viewBox="0 0 24 24"
        >
          <circle
            cx="12"
            cy="12"
            r="9"
            fill="none"
            stroke="currentColor"
            opacity=".18"
            strokeWidth="3"
          />
          <circle
            cx="12"
            cy="12"
            r="9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            pathLength="100"
            strokeDasharray={`${(work.completed / work.total) * 100} 100`}
            transform="rotate(-90 12 12)"
          />
        </svg>
      )}
    </span>
  );
}
