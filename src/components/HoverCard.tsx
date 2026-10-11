import {
  cloneElement,
  isValidElement,
  useId,
  useRef,
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
    timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const [position, setPosition] = useState<{
    top: number;
    left: number;
    above: boolean;
  } | null>(null);
  const open = () => {
    clearTimeout(timer.current);
    const r = anchor.current?.getBoundingClientRect();
    if (r)
      setPosition({
        top: r.bottom + 9,
        left: Math.max(10, Math.min(innerWidth - 310, r.left)),
        above: r.bottom > innerHeight * 0.55,
      });
  };
  const close = () => {
    timer.current = setTimeout(() => setPosition(null), 130);
  };
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
            id={id}
            role="tooltip"
            className="hover-card"
            onMouseEnter={() => clearTimeout(timer.current)}
            onMouseLeave={close}
            style={{
              left: position.left,
              ...(position.above
                ? { bottom: innerHeight - position.top + 26 }
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
    "What might the author be trying to accomplish here? These are revisable interpretations supplied by the analysis, grounded in its evidence. Word size follows declared likelihood when available, otherwise relative support. Shared goals keep their place as you move between sentences. Select a goal to inspect its sources.",
  process:
    "A hierarchy of possible goals: the broad purpose is on the right; subordinate goals branch toward individual sentences on the left. Hover a block to trace its ancestors and descendants. Hover page text to roll through the corresponding goal spools. Double-click a sentence to lock; Escape releases. This hierarchy does not establish the historical order of writing.",
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
      <HoverCard content={<p>{explanations[kind]}</p>}>
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
