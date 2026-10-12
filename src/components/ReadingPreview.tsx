import { ReadingText, textOffset } from "./ReadingText";
import { ghostAt } from "../core/ghost";
import type { Artifact, Packet } from "../core/model";
import { sentences } from "../core/sentences";
import { SelectionLock } from "./SelectionLock";
export function ReadingPreview({
  artifact,
  packet,
  maker,
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
  packet?: Packet | null;
  maker?: string;
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
                    onMove(
                      r.id,
                      false,
                      s.start +
                        textOffset(
                          e.currentTarget,
                          e.clientX,
                          e.clientY,
                          s.text.length,
                        ),
                    );
                  }}
                  onFocus={() => onMove(r.id, false, s.start)}
                  onClick={(e) => {
                    if (!getSelection()?.toString()) {
                      onMove(
                        r.id,
                        true,
                        s.start +
                          textOffset(
                            e.currentTarget,
                            e.clientX,
                            e.clientY,
                            s.text.length,
                          ),
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
                  <ReadingText
                    text={s.text}
                    start={s.start}
                    emphasis={r.emphasis}
                    reading={ghostAt(packet, maker, r.id, s.start, s.end)}
                    packet={packet}
                  />
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
