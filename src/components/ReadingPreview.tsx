import type { Artifact } from "../core/model";
import { sentences } from "../core/sentences";
import { SelectionLock } from "./SelectionLock";
export function ReadingPreview({
  artifact,
  region,
  offset,
  pinned,
  active,
  onMove,
  onLeave,
  onUnlock,
  lockReminder = 0,
}: {
  artifact: Artifact;
  region: string;
  offset: number;
  pinned: boolean;
  active: boolean;
  onMove: (id: string, pin?: boolean, offset?: number) => void;
  onLeave: () => void;
  onUnlock: () => void;
  lockReminder?: number;
}) {
  return (
    <main className="example-page saved-page">
      <header>Saved reading · {artifact.source}</header>
      <article onMouseLeave={onLeave}>
        {artifact.regions.map((r) => (
          <p key={r.id} data-passage={r.id}>
            {sentences(r.anchor.exact).map((s, i) => (
              <span key={s.start}>
                <span
                  data-sentence={i}
                  tabIndex={0}
                  className={
                    active &&
                    region === r.id &&
                    offset >= s.start &&
                    offset < s.end
                      ? "active-sentence"
                      : ""
                  }
                  onMouseMove={(e) => {
                    const caret = document.caretRangeFromPoint(
                      e.clientX,
                      e.clientY,
                    );
                    onMove(
                      r.id,
                      false,
                      s.start +
                        (caret?.startContainer === e.currentTarget.firstChild
                          ? Math.min(caret.startOffset, s.text.length - 1)
                          : 0),
                    );
                  }}
                  onFocus={() => onMove(r.id, false, s.start)}
                  onClick={(e) => {
                    if (!getSelection()?.toString()) {
                      const caret = document.caretRangeFromPoint(
                        e.clientX,
                        e.clientY,
                      );
                      onMove(
                        r.id,
                        true,
                        s.start +
                          (caret?.startContainer === e.currentTarget.firstChild
                            ? Math.min(caret.startOffset, s.text.length - 1)
                            : 0),
                      );
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onMove(r.id, true, s.start);
                    }
                  }}
                >
                  {s.text}
                </span>
                {pinned &&
                  region === r.id &&
                  offset >= s.start &&
                  offset < s.end && (
                    <SelectionLock
                      className="inline-lock"
                      reminder={lockReminder}
                      onUnlock={onUnlock}
                    />
                  )}{" "}
              </span>
            ))}
          </p>
        ))}
      </article>
    </main>
  );
}
