import {
  contextBrief,
  contextTimeline,
  dateKindLabel,
  type ContextReport,
} from "../core/author-context";
import type { ContextItem } from "../core/model";
function sourceLink(value: string) {
  try {
    const u = new URL(value);
    return ["https:", "http:"].includes(u.protocol) &&
      !u.username &&
      !u.password
      ? u.href
      : undefined;
  } catch {
    return;
  }
}
export function ContextTimeline({
  items,
  author,
  report,
  onSelect,
  onRefresh,
  onClear,
  busy,
}: {
  items: ContextItem[];
  author: string;
  report: ContextReport | null;
  onSelect: (id: string, selected: boolean) => void;
  onRefresh: () => void;
  onClear: () => void;
  busy: boolean;
}) {
  const timeline = contextTimeline(items, author);
  const render = (f: (typeof timeline.dated)[number], i: number) => (
    <li key={`${f.itemId}:${i}`}>
      <div className="timeline-date">
        <span>{f.date ?? "Undated"}</span>
        <small>{dateKindLabel[f.dateKind]}</small>
      </div>
      <div>
        <strong>{f.label}</strong>
        <details>
          <summary>Source and excerpt</summary>
          <blockquote>{f.quote}</blockquote>
          <a href={sourceLink(f.source)} target="_blank" rel="noreferrer">
            {f.source}
          </a>
          <small>
            Retrieved {new Date(f.retrievedAt).toLocaleString()} ·{" "}
            {f.basis.replaceAll("-", " ")}
            {f.linkedFrom ? ` · linked from ${f.linkedFrom}` : ""}
          </small>
        </details>
      </div>
    </li>
  );
  return (
    <div className="context-timeline">
      <p>
        Source-backed context for <strong>{author}</strong>. Linked publications
        and profile timestamps are not a verified biography.
      </p>
      <div className="timeline-actions">
        <button disabled={busy} onClick={onRefresh}>
          Refresh sources
        </button>
        <button
          disabled={!timeline.sources.length}
          onClick={() => {
            const blob = new Blob([contextBrief(items, author)], {
                type: "text/plain;charset=utf-8",
              }),
              url = URL.createObjectURL(blob),
              a = document.createElement("a");
            a.href = url;
            a.download = "tompathy-author-context.txt";
            a.click();
            setTimeout(() => URL.revokeObjectURL(url), 1000);
          }}
        >
          Export brief
        </button>
        <button disabled={busy} onClick={onClear}>
          Clear context
        </button>
      </div>
      {report && (
        <p className="muted" role="status">
          {report.collected} of {report.attempted} sources read ·{" "}
          {report.cached} cached · {report.skipped.length} links outside this
          collection.
        </p>
      )}
      {report && !!(report.failures.length + report.skipped.length) && (
        <details>
          <summary>Collection coverage</summary>
          <ul>
            {[...report.failures, ...report.skipped].map((r, i) => (
              <li key={i}>
                {r.source} — {r.reason}
              </li>
            ))}
          </ul>
        </details>
      )}
      <h3>Timeline</h3>
      {timeline.dated.length ? (
        <ol>{timeline.dated.map(render)}</ol>
      ) : (
        <p className="muted">
          No explicit dates found. No chronology has been inferred.
        </p>
      )}
      <h3>Undated context</h3>
      {timeline.undated.length ? (
        <ol>{timeline.undated.map(render)}</ol>
      ) : (
        <p className="muted">
          Enable Light context to collect the page byline and linked sources.
        </p>
      )}
      {!!timeline.sources.length && (
        <details className="context-use">
          <summary>Sources for the next analysis</summary>
          <p>
            Only checked sources enter an exported analysis request. Changing
            the selection requires a matching analysis revision.
          </p>
          {timeline.sources.map((s) => (
            <label key={s.id}>
              <input
                type="checkbox"
                checked={s.selected}
                onChange={(e) => onSelect(s.id, e.target.checked)}
              />
              <span>{s.source}</span>
            </label>
          ))}
        </details>
      )}
    </div>
  );
}
