import {
  cloneElement,
  isValidElement,
  useId,
  useRef,
  useEffect,
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
        if (e.key === "Escape" && position) {
          e.stopPropagation();
          setPosition(null);
        }
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
    "What might be occupying the creator’s attention at this point in the text? These supplied interpretations are independent of the goal hierarchy. For a sentence, word size and boldness follow supplied likelihood or relative support. For a broader branch, size and boldness combine how often a focus occurs with its supplied confidence, giving each sentence equal weight. Shared sentences count once; unscored items receive no invented confidence. Only the strongest phrases that comfortably fit are shown; the full ranking remains in the supplied data. Hover a phrase for its coverage and evidence. The strongest item gathers near the center; shared phrases persist while newcomers bubble into place. Click to hold a selection. The example uses hand-written snapshots, not live inference.",
  process:
    "Expertise is a kind of lossy, compressed record of all of the creator’s previous attentional focuses — nerves that fired together, wired together. This is the project’s conceptual model. A hierarchy of possible goals: possible broader ends are on the right; subordinate goals branch toward individual sentences on the left. Hover a block to trace its ancestors and descendants. Hover page text to roll through the corresponding goal spools. Click a sentence or block to lock; either green lock or Escape releases. Scroll a reel to explore neighboring goals at that level. Drag a vertical tier boundary to resize adjacent layers; focus a separator and use left/right arrows for the same adjustment, or Home to reset. The widest initial tier favors a useful intermediate level. The triangle stays visible throughout. This hierarchy does not establish the historical order of writing.",
  values:
    "‘Core values’ is shorthand; the project prefers ‘latent preferences.’ Working model: compare a person’s initial situation with the changes their actions appear to seek. Correlate those observations with their history to suggest preferred states, or a homeostatic range, rather than reading motives directly from a sentence. That preferred range may drift over a lifetime; it is a trajectory, not a fixed target. The curve depicts a proposed preferred state; its tube depicts uncertainty. Each numbered vector starts at an observed or inferred state and points toward a sought change. Its angle suggests how far into the future the reward is sought; its reach and weight suggest the cost the person may accept to move toward that state. Tube shading echoes that proposed strength. Each vector has its own observation below the graph. On the website demo, a rising contour current marks a drive and layered currents mark a constructed value; the seven drives follow Panksepp’s proposed systems, with PANIC/GRIEF displayed here as Belonging. The miniature brain sketches show approximate networks, not a measurement of this creator’s brain. Constructed entries are a prototype inspired by Barrett’s account, not a claim that the two theories form a single established taxonomy. Current work only, Creator and Global supply different demo perspectives. Current work only concerns evidence from this page; Creator concerns the person across works; Global is a broader catalogue for this prototype. The straight confidence arrow in the card and the label’s boldness represent confidence in the preference account, independently of the strength of the preference. Research caution: homeostatic models have a basis in physiological regulation. Extending them to abstract personal values, equating vector angle with a discount rate, and inferring willingness to pay from prose remain proposals here. Actions can also reflect constraints, habits or other goals; they do not uniquely identify a latent preference. These demo trajectories and confidence scores are authored illustrations, not measurements.",
};
export function SectionTitle({
  kind,
  children,
  onOpen,
}: {
  kind: keyof typeof explanations;
  children: ReactNode;
  onOpen: () => void;
}) {
  const openTimer = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  );
  useEffect(() => () => clearTimeout(openTimer.current), []);
  return (
    <h2 id={`${kind}-title`}>
      <HoverCard
        content={
          kind === "process" ? (
            <>
              <strong className="expertise-thesis">
                Expertise is a kind of lossy, compressed record of all of the
                creator’s previous attentional focuses — nerves that fired
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
                Each sentence has one cell. A connecting line reveals an
                additional supplied parent when that relationship is inspected.
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
                measurement of the creator’s nerves.
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
          aria-haspopup="dialog"
          onClick={(e) => {
            clearTimeout(openTimer.current);
            if (e.detail === 0) onOpen();
            // Leave a double-click available for the reader's global unlock.
            else if (e.detail === 1)
              openTimer.current = setTimeout(onOpen, 500);
          }}
          onDoubleClick={() => clearTimeout(openTimer.current)}
          onBlur={() => clearTimeout(openTimer.current)}
          onKeyDown={(e) => {
            if (e.key === "Escape") clearTimeout(openTimer.current);
          }}
        >
          {children}
        </button>
      </HoverCard>
    </h2>
  );
}
