import { useRef, useState } from "react";
import { Search, X } from "lucide-react";
export type ValuesTab = "work" | "creator" | "global";
const tabs = ["work", "creator", "global"] as const;
export function ValueTabs({
  tab,
  onTab,
}: {
  tab: ValuesTab;
  onTab: (tab: ValuesTab) => void;
}) {
  const [search, setSearch] = useState(false),
    [query, setQuery] = useState(""),
    [submitted, setSubmitted] = useState(false);
  const button = useRef<HTMLButtonElement>(null);
  const close = () => {
    setSearch(false);
    setSubmitted(false);
    requestAnimationFrame(() => button.current?.focus());
  };
  return (
    <div className={`value-tabs ${search ? "searching" : ""}`}>
      <div role="tablist" aria-label="Values perspective">
        {tabs.map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            aria-controls="values-view"
            tabIndex={tab === t ? 0 : -1}
            onKeyDown={(e) => {
              if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key))
                return;
              e.preventDefault();
              const next =
                tabs[
                  e.key === "Home"
                    ? 0
                    : e.key === "End"
                      ? 2
                      : (tabs.indexOf(t) + (e.key === "ArrowRight" ? 1 : 2)) % 3
                ];
              onTab(next);
              const buttons =
                e.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>(
                  '[role="tab"]',
                );
              buttons?.[tabs.indexOf(next)]?.focus();
            }}
            onClick={() => onTab(t)}
          >
            {t === "work" ? "current work only" : t}
          </button>
        ))}
      </div>
      <button
        ref={button}
        className="search-toggle"
        aria-label="Open search preview"
        title="Search · interface preview"
        aria-expanded={search}
        aria-controls="values-search"
        onClick={() => (search ? close() : setSearch(true))}
      >
        <Search size={15} aria-hidden="true" />
      </button>
      {search && (
        <form
          id="values-search"
          className="value-search"
          onSubmit={(e) => {
            e.preventDefault();
            setSubmitted(true);
          }}
        >
          <input
            autoFocus
            aria-label="Search preview"
            placeholder="Search…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSubmitted(false);
            }}
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                e.stopPropagation();
                close();
              }
            }}
          />
          <button type="button" aria-label="Close search" onClick={close}>
            <X size={13} />
          </button>
          <span className="sr-only" role="status">
            {submitted ? "Search preview only. No query was sent." : ""}
          </span>
        </form>
      )}
    </div>
  );
}
