import { useEffect, useState } from "react";
import { SessionSchema, type Session } from "../core/model";
import { isExtension } from "../browser";
export function SavedPage() {
  const [session, setSession] = useState<Session | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const key = `snapshot:${new URLSearchParams(location.search).get("id")}`;
        const stored = isExtension
          ? (await chrome.storage.session.get(key))[key]
          : JSON.parse(sessionStorage.getItem(key) ?? "null");
        const s = SessionSchema.parse(stored);
        if (!s.artifact) throw Error("No saved page in this reading.");
        if (alive) setSession(s);
      } catch {
        if (alive)
          setError(
            "This saved reading is no longer in this browser session. Import its file again.",
          );
      }
    })();
    return () => {
      alive = false;
    };
  }, []);
  useEffect(() => {
    if (!session || !isExtension) return;
    window.__tompathySnapshot = session;
    void import("../content").then(async ({ installPageAdapter }) => {
      installPageAdapter();
      const tab = await chrome.tabs.getCurrent();
      void chrome.runtime
        .sendMessage({ type: "TOMPATHY_INVOKED", tabId: tab?.id })
        .catch(() => {});
    });
    return () => {
      window.__tompathyCleanup?.();
      delete window.__tompathySnapshot;
    };
  }, [session]);
  return (
    <main className="saved-page">
      <header data-tompathy-ui>
        <span>Saved reading · {session?.artifact?.source}</span>
        {isExtension && (
          <button
            onClick={async () => {
              const tab = await chrome.tabs.getCurrent();
              if (tab?.id) await chrome.sidePanel.open({ tabId: tab.id });
            }}
          >
            Open ToMpathy
          </button>
        )}
        <small>
          Readable text snapshot · original styling and interactive page
          features are not included.
        </small>
      </header>
      {error && <p role="alert">{error}</p>}
      <article>
        {session?.artifact?.regions.map((r) => (
          <p key={r.id} data-snapshot-region={r.id} tabIndex={0}>
            {r.anchor.exact}
          </p>
        ))}
      </article>
    </main>
  );
}
