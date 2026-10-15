import { artSnapshot } from "../core/art-example";
import { ReadingText } from "./ReadingText";
import { isExtension } from "../browser";

/** Safe static rendering: no original scripts or HTML are inserted. */
export function ArtArticle() {
  return (
    <main className="example-page art-page-snapshot">
      <header data-tompathy-ui>
        <div>
          <a href={artSnapshot.source} target="_blank" rel="noreferrer">
            Abraham Haskins · original essay ↗
          </a>
          <span>Public text · creator disclosures · editorial demo</span>
        </div>
        {isExtension && (
          <button
            onClick={async () => {
              const tab = await chrome.tabs.getCurrent();
              if (tab?.id) await chrome.sidePanel.open({ tabId: tab.id });
            }}
          >
            Open Maker Reader
          </button>
        )}
      </header>
      <article>
        {artSnapshot.blocks.map((b, i) => {
          const Tag =
            b.type === "title"
              ? "h1"
              : b.type === "section"
                ? "h2"
                : b.type === "heading"
                  ? "h3"
                  : b.type === "equation"
                    ? "pre"
                    : "p";
          return (
            <Tag
              key={i}
              data-passage={`p${i + 1}`}
              className={`art-block-${b.type}`}
            >
              <ReadingText
                text={b.text}
                emphasis={b.emphasis}
                annotate={false}
              />
            </Tag>
          );
        })}
      </article>
      <footer data-tompathy-ui>
        {artSnapshot.note}{" "}
        <a href={artSnapshot.source} target="_blank" rel="noreferrer">
          Read the original ↗
        </a>
      </footer>
    </main>
  );
}
