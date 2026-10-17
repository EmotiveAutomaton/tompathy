import {
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { CircleHelp } from "lucide-react";
import { essayLabels, type EssayKind } from "../content/essay-kind";

export function SectionTitle({
  kind,
  children,
  onOpen,
}: {
  kind: EssayKind;
  children: ReactNode;
  onOpen: () => void;
}) {
  const [open, setOpen] = useState(false);
  const button = useRef<HTMLButtonElement>(null),
    card = useRef<HTMLDivElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const id = useId();
  const show = () => {
    window.dispatchEvent(
      new CustomEvent("tompathy-section-preview", { detail: id }),
    );
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setOpen(true), 1500);
  };
  const hide = () => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setOpen(false), 180);
  };
  const dismiss = () => {
    clearTimeout(timer.current);
    setOpen(false);
  };
  useEffect(() => () => clearTimeout(timer.current), []);
  useEffect(() => {
    const anotherPreview = (e: Event) => {
      if ((e as CustomEvent).detail !== id) dismiss();
    };
    window.addEventListener("tompathy-section-preview", anotherPreview);
    return () =>
      window.removeEventListener("tompathy-section-preview", anotherPreview);
  }, [id]);
  useEffect(() => {
    if (!open) return;
    const escape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        dismiss();
      }
    };
    const scroll = () => dismiss();
    window.addEventListener("keydown", escape, true);
    window.addEventListener("resize", scroll);
    return () => {
      window.removeEventListener("keydown", escape, true);
      window.removeEventListener("resize", scroll);
    };
  }, [open]);
  useLayoutEffect(() => {
    if (!open || !button.current || !card.current) return;
    const anchor = button.current.getBoundingClientRect(),
      el = card.current;
    const zoom =
      Number.parseFloat(getComputedStyle(document.documentElement).zoom) || 1;
    el.style.width = `${Math.min(260, innerWidth - 24) / zoom}px`;
    el.style.maxHeight = `${(innerHeight - 24) / zoom}px`;
    const rect = el.getBoundingClientRect();
    el.style.left = `${Math.max(12, Math.min(innerWidth - rect.width - 12, anchor.left)) / zoom}px`;
    el.style.top = `${Math.max(12, Math.min(innerHeight - rect.height - 12, anchor.bottom + 8)) / zoom}px`;
  }, [open]);
  return (
    <h2
      id={`${kind}-title`}
      className="essay-section-title"
      aria-label={essayLabels[kind]}
    >
      <span>{children}</span>
      <button
        ref={button}
        className="section-question"
        aria-label={`About ${essayLabels[kind]}`}
        aria-haspopup="dialog"
        aria-describedby={open ? id : undefined}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={(e) => {
          if (!card.current?.contains(e.relatedTarget)) dismiss();
        }}
        onDoubleClick={(e) => e.stopPropagation()}
        onClick={() => {
          dismiss();
          onOpen();
        }}
      >
        <CircleHelp size={14} aria-hidden="true" />
      </button>
      {open &&
        createPortal(
          <div
            ref={card}
            role="tooltip"
            id={id}
            className="essay-preview"
            onMouseEnter={() => clearTimeout(timer.current)}
            onMouseLeave={hide}
            onFocus={show}
            onBlur={(e) => {
              if (
                !card.current?.contains(e.relatedTarget) &&
                e.relatedTarget !== button.current
              )
                dismiss();
            }}
          >
            <p>
              {kind === "goals"
                ? "Click for a fun explanation"
                : `Click for part ${kind === "process" ? "two" : "three"} of a cool`}
              <br />
              {kind === "goals"
                ? "of why this works."
                : "explanation of why this works."}
            </p>
          </div>,
          document.body,
        )}
    </h2>
  );
}
