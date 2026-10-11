import {
  cloneElement,
  isValidElement,
  useId,
  useRef,
  useLayoutEffect,
  useState,
  type ReactNode,
  type ReactElement,
} from "react";
import { createPortal } from "react-dom";

/** The same explanation is available to mouse, keyboard and touch users. */
export function HoverCard({
  children,
  content,
  className = "",
}: {
  children: ReactNode;
  content: ReactNode;
  className?: string;
}) {
  const id = useId(),
    anchor = useRef<HTMLSpanElement>(null),
    card = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<{
    top: number;
    left: number;
    above: boolean;
    anchorTop: number;
  } | null>(null);
  const open = () => {
    const r = anchor.current?.getBoundingClientRect();
    if (r)
      setPosition({
        top: r.bottom + 9,
        anchorTop: r.top,
        left: Math.max(10, Math.min(innerWidth - 570, r.left)),
        above: r.bottom > innerHeight * 0.55,
      });
  };
  const close = () => {
    setPosition(null);
  };
  useLayoutEffect(() => {
    const el = card.current;
    if (!el || !position) return;
    const r = el.getBoundingClientRect();
    if (r.top < 10) {
      el.style.bottom = "auto";
      el.style.top = "10px";
    } else if (r.bottom > innerHeight - 10) {
      el.style.bottom = "10px";
      el.style.top = "auto";
    }
  }, [position]);
  return (
    <span
      ref={anchor}
      className={`hover-anchor ${className}`}
      onMouseEnter={open}
      onMouseLeave={close}
      onFocus={open}
      onBlur={close}
      onKeyDown={(e) => {
        if (e.key === "Escape") setPosition(null);
      }}
      aria-describedby={position ? id : undefined}
    >
      {isValidElement(children)
        ? cloneElement(
            children as ReactElement<{ "aria-describedby"?: string }>,
            { "aria-describedby": position ? id : undefined },
          )
        : children}
      {position &&
        createPortal(
          <div
            ref={card}
            id={id}
            role="tooltip"
            className="hover-card"
            style={{
              left: position.left,
              ...(position.above
                ? { bottom: innerHeight - position.anchorTop + 8 }
                : { top: position.top }),
            }}
          >
            {content}
          </div>,
          document.body,
        )}
    </span>
  );
}
export const explanations = {
  goals:
    "What might be occupying the author’s attention at this point in the text? These supplied interpretations are independent of the goal hierarchy. Word size follows declared likelihood when available, otherwise relative support. The strongest current item gathers near the center; shared phrases persist while newcomers bubble into place. Hover text or a sentence brick to reveal attention. Click to hold it, then select a phrase for its evidence. The example uses hand-authored snapshots, not live inference.",
  process:
    "Expertise is a kind of lossy, compressed record of all of the author’s previous attentional focuses — nerves that fired together, wired together. This is the project’s conceptual model. A hierarchy of possible goals: possible broader ends are on the right; subordinate goals branch toward individual sentences on the left. Hover a block to trace its ancestors and descendants. Hover page text to roll through the corresponding goal spools. Click a sentence or block to lock; either green lock or Escape releases. Scroll a reel to explore neighboring goals at that level. The triangle stays visible throughout. This hierarchy does not establish the historical order of writing.",
  values:
    "Recurring latent preferences that may explain the author’s choices across this text and any explicitly selected context. The creator considers ‘core values’ imprecise; ‘latent preferences’ is the preferred term. Wheels show the supplied support, not an invented confidence score. Hover a row for sources. Values stay steady until you accept a new account.",
};
export function SectionTitle({
  kind,
  children,
}: {
  kind: keyof typeof explanations;
  children: ReactNode;
}) {
  return (
    <h2 id={`${kind}-title`}>
      <HoverCard
        content={
          kind === "process" ? (
            <>
              <strong className="expertise-thesis">
                Expertise is a kind of lossy, compressed record of all of the
                author’s previous attentional focuses — nerves that fired
                together, wired together.
              </strong>
              <p className="muted">A conceptual lens for this project.</p>
              <svg
                className="hierarchy-key"
                viewBox="0 0 360 75"
                role="img"
                aria-label="Many local attentional choices feed into fewer habits and broader goals"
              >
                <path
                  d="M12 6 Q170 8 345 37 Q170 68 12 69 Z"
                  fill="currentColor"
                  opacity=".12"
                />
                {[16, 30, 44, 58].map((y) => (
                  <path
                    key={y}
                    d={`M28 ${y} L132 ${y < 37 ? 24 : 51} L230 37 L325 37`}
                    stroke="currentColor"
                    fill="none"
                    opacity=".45"
                  />
                ))}
                {[16, 30, 44, 58].map((y) => (
                  <circle key={y} cx="28" cy={y} r="3" fill="currentColor" />
                ))}
                <circle cx="132" cy="24" r="4" fill="currentColor" />
                <circle cx="132" cy="51" r="4" fill="currentColor" />
                <circle cx="230" cy="37" r="5" fill="currentColor" />
                <circle cx="325" cy="37" r="5" fill="currentColor" />
              </svg>
              <p>
                Local choices on the left feed into broader goals on the right.
                Hover a brick to trace both its ancestors and its possible
                subordinate goals; the same green connects them to the page.
              </p>
              <p>
                Click text or a brick to hold a selection. Scroll a reel, or
                focus it and use ↑ / ↓, to explore that level. Blurred reels
                represent multiple possible descendants, broader goals or
                earlier endings. A shorter peak ends before the tallest one. The
                hovered brick’s reel glows. Click either green lock, or press
                Escape, to release the selection.
              </p>
              <p className="muted">
                Depth comes from the supplied hierarchy. These are
                interpretations, not an established writing history or a
                measurement of the author’s nerves.
              </p>
            </>
          ) : (
            <p>{explanations[kind]}</p>
          )
        }
      >
        <button
          className="heading-help"
          aria-label={`About ${typeof children === "string" ? children : kind}`}
        >
          {children}
        </button>
      </HoverCard>
    </h2>
  );
}
