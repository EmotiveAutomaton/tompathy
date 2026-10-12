import { useRef, useState } from "react";
import { Search, X } from "lucide-react";
export function ValueTabs({
  tab,
  onTab,
}: {
  tab: "author" | "global";
  onTab: (tab: "author" | "global") => void;
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
        {(["author", "global"] as const).map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            aria-controls="values-view"
            onClick={() => onTab(t)}
          >
            {t}
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
