import { Fragment, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import {
  essays,
  bibliography,
  essayLabels,
  type EssayKind,
  type EssayPage,
} from "../content/essays";
import {
  figuresFor,
  type EssayFigure,
  type Illustration,
} from "../content/essay-figures";
import { DriveBrain } from "./DriveBrain";
import { driveSystems } from "../core/drive-systems";
import { PreferenceChart } from "./PreferenceChart";
import { demoPreference } from "../core/example-values";
import "../essay.css";

export function EssayText({ kind, text }: { kind: EssayKind; text: string }) {
  // Close whitespace before superscripts, retaining the space before the next word.
  const parts = text
    .replace(/\s+(?=\[\d+\])/g, "")
    .split(/(\[\d+\]|\[abrahamhaskins\.org\/art\]|\*[^*]+\*)/g);
  return (
    <>
      {parts.map((part, i) => {
        const citation = part.match(/^\[(\d+)\]$/);
        if (citation) {
          const reference = essays[kind].references[citation[1]];
          const adjacent =
            i >= 2 && /^\[\d+\]$/.test(parts[i - 2]) && parts[i - 1] === "";
          return (
            <sup className="essay-citation" key={i}>
              {adjacent && <span aria-hidden="true">,</span>}
              <a
                href={reference.href}
                target="_blank"
                rel="noopener noreferrer"
                title={reference.text}
                aria-label={`${reference.number}. ${reference.text}`}
              >
                {reference.number}
              </a>
            </sup>
          );
        }
        if (part === "[abrahamhaskins.org/art]")
          return (
            <a
              key={i}
              href="https://abrahamhaskins.org/art/"
              target="_blank"
              rel="noopener noreferrer"
            >
              abrahamhaskins.org/art
            </a>
          );
        if (part.startsWith("*") && part.endsWith("*"))
          return <em key={i}>{part.slice(1, -1)}</em>;
        return part;
      })}
    </>
  );
}

type ExpandedImage =
  Illustration | { diagram: "channels" | "preference"; name: string };

function ImageLightbox({
  image,
  onClose,
}: {
  image: ExpandedImage;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const prior = document.activeElement as HTMLElement | null;
    const el = dialog.current!;
    const overflow = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    el.showModal();
    return () => {
      el.close();
      document.documentElement.style.overflow = overflow;
      if (prior?.isConnected) prior.focus({ preventScroll: true });
    };
  }, []);
  return createPortal(
    <dialog
      ref={dialog}
      className="essay-lightbox"
      aria-label={image.name}
      onClick={(e) => {
        e.stopPropagation();
        onClose();
      }}
      onCancel={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }}
      onKeyDown={(e) => {
        e.stopPropagation();
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClose();
        }
      }}
    >
      {"src" in image ? (
        <img src={image.src} alt={image.name} />
      ) : (
        <Diagram kind={image.diagram} />
      )}
    </dialog>,
    document.body,
  );
}

function Figure({
  kind,
  figure,
  onExpand,
}: {
  kind: EssayKind;
  figure: EssayFigure;
  onExpand: (image: ExpandedImage) => void;
}) {
  return (
    <figure
      className={`essay-figure ${figure.large ? "essay-figure-large" : ""} ${(figure.images?.length ?? 0) > 1 || figure.diagram === "channels" ? "essay-figure-group" : ""} ${figure.images?.length === 4 ? "essay-figure-four" : ""}`}
      data-figure-anchor={figure.anchor}
    >
      {figure.images && (
        <div
          className={`essay-images ${figure.images.length > 1 ? "essay-image-grid" : ""} ${figure.portrait ? "essay-portraits" : ""}`}
        >
          {figure.images.map((image) => (
            <button
              type="button"
              className="essay-image-button"
              key={image.src}
              aria-label={`Enlarge ${image.name}`}
              onClick={() => onExpand(image)}
            >
              <img
                src={image.src}
                alt={image.name}
                title={image.name}
                loading="lazy"
                decoding="async"
                className={
                  (image.uncropped ? "essay-uncropped-image " : "") +
                  (image.borderless
                    ? "essay-borderless-image"
                    : image.generated
                      ? "essay-generated-image"
                      : "essay-human-image")
                }
              />
            </button>
          ))}
        </div>
      )}
      {figure.diagram && (
        <button
          className="essay-diagram-button"
          type="button"
          aria-label={`Enlarge ${figure.diagram === "channels" ? "seven channels" : "preference vectors"}`}
          onClick={() =>
            onExpand({
              diagram: figure.diagram!,
              name:
                figure.diagram === "channels"
                  ? "Seven channels"
                  : "Preference vectors and uncertainty sleeve",
            })
          }
        >
          <Diagram kind={figure.diagram} />
        </button>
      )}
      {figure.caption && (
        <figcaption>
          <p>
            <EssayText kind={kind} text={figure.caption} />
          </p>
        </figcaption>
      )}
    </figure>
  );
}

function Diagram({ kind }: { kind: "channels" | "preference" }) {
  return kind === "channels" ? (
    <div className="essay-channels" title="Seven channels">
      {Object.keys(driveSystems).map((label) => (
        <div className="essay-channel" key={label}>
          <DriveBrain
            h={{ label, valueCategory: "drive" }}
            title={label === "Belonging" ? "PANIC/GRIEF" : label}
          />
          <span>{label === "Belonging" ? "PANIC/GRIEF" : label}</span>
        </div>
      ))}
    </div>
  ) : (
    <div
      className="essay-preference"
      role="img"
      aria-label="Illustrative preference vectors and uncertainty sleeve from the existing demo"
      title="Preference vectors and uncertainty sleeve"
    >
      <div inert>
        <PreferenceChart trace={demoPreference("care")!} />
      </div>
    </div>
  );
}

export function EssaySurface({
  kind,
  onClose,
  onNavigate,
  onLightboxChange,
}: {
  kind: EssayPage;
  onClose: () => void;
  onNavigate: (page: EssayPage) => void;
  onLightboxChange?: (open: boolean) => void;
}) {
  const [expanded, setExpanded] = useState<ExpandedImage | null>(null);
  const openImage = (image: ExpandedImage) => {
    setExpanded(image);
    onLightboxChange?.(true);
  };
  const closeImage = () => {
    setExpanded(null);
    onLightboxChange?.(false);
  };
  const surface = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const dialog = surface.current?.closest(".essay-dialog");
    if (dialog) dialog.scrollTop = 0;
    else window.scrollTo(0, 0);
  }, [kind]);
  const next: EssayPage | null =
    kind === "goals" ? "process" : kind === "process" ? "values" : null;
  return (
    <div
      ref={surface}
      className="essay-surface"
      onDoubleClick={(e) => e.stopPropagation()}
    >
      {expanded && <ImageLightbox image={expanded} onClose={closeImage} />}
      <header className="essay-header">
        <h1>
          {kind === "bibliography" ? essayLabels[kind] : essays[kind].title}
        </h1>
        <button
          className="essay-close"
          aria-label="Close essay"
          onClick={onClose}
          autoFocus
        >
          <X size={21} />
        </button>
      </header>
      <article className="essay-prose" aria-label={essayLabels[kind]}>
        {(kind === "process" || kind === "values") && (
          <p className="essay-navigation">
            (first essay{" "}
            <a
              href="?section=goals"
              onClick={(e) => {
                e.preventDefault();
                onNavigate("goals");
              }}
            >
              here
            </a>
            )
          </p>
        )}
        {kind === "bibliography" ? (
          <ol className="essay-bibliography">
            {bibliography.map((ref) => (
              <li key={ref.number} value={ref.number}>
                <a href={ref.href} target="_blank" rel="noopener noreferrer">
                  {ref.text}
                </a>
              </li>
            ))}
          </ol>
        ) : (
          essays[kind].paragraphs.map((paragraph, index) => (
            <Fragment key={index}>
              {figuresFor(kind, paragraph.text, "before").map((f) => (
                <Figure
                  key={f.anchor}
                  kind={kind}
                  figure={f}
                  onExpand={openImage}
                />
              ))}
              <p data-essay-paragraph={index}>
                <EssayText kind={kind} text={paragraph.text} />
              </p>
              {figuresFor(kind, paragraph.text, "after").map((f) => (
                <Figure
                  key={f.anchor}
                  kind={kind}
                  figure={f}
                  onExpand={openImage}
                />
              ))}
            </Fragment>
          ))
        )}
        {next && (
          <p className="essay-navigation essay-next">
            <a
              href={`?section=${next}`}
              onClick={(e) => {
                e.preventDefault();
                onNavigate(next);
              }}
            >
              next
            </a>
          </p>
        )}
      </article>
    </div>
  );
}

export function EssayDialog({
  kind,
  onClose,
}: {
  kind: EssayPage;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const outside = useRef(false);
  const [page, setPage] = useState(kind);
  useEffect(() => {
    const prior = document.activeElement as HTMLElement | null;
    const el = dialog.current!;
    const fit = () => {
      const zoom =
        Number.parseFloat(getComputedStyle(document.documentElement).zoom) || 1;
      el.style.width = `${((visualViewport?.width ?? innerWidth) - 48) / zoom}px`;
      el.style.maxHeight = `${((visualViewport?.height ?? innerHeight) - 48) / zoom}px`;
    };
    fit();
    el.showModal();
    window.addEventListener("resize", fit);
    visualViewport?.addEventListener("resize", fit);
    return () => {
      el.close();
      if (prior?.isConnected) prior.focus();
      window.removeEventListener("resize", fit);
      visualViewport?.removeEventListener("resize", fit);
    };
  }, []);
  const isOutside = (x: number, y: number) => {
    const r = dialog.current!.getBoundingClientRect();
    return x < r.left || x > r.right || y < r.top || y > r.bottom;
  };
  return createPortal(
    <dialog
      ref={dialog}
      className="essay-dialog"
      aria-label={essayLabels[page]}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape") e.stopPropagation();
      }}
      onPointerDown={(e) => {
        outside.current = isOutside(e.clientX, e.clientY);
      }}
      onClick={(e) => {
        if (outside.current && isOutside(e.clientX, e.clientY)) onClose();
      }}
    >
      <EssaySurface kind={page} onClose={onClose} onNavigate={setPage} />
    </dialog>,
    document.body,
  );
}
