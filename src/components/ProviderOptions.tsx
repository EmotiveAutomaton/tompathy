import { useState } from "react";
import { isExtension } from "../browser";
import {
  checkCompanion,
  providerOrigin,
  type ProviderSettings,
} from "../core/provider";

const key = "tompathy-provider";
export async function readProvider(): Promise<ProviderSettings> {
  try {
    const value = isExtension
      ? (await chrome.storage.local.get(key))[key]
      : JSON.parse(localStorage.getItem(key) ?? "null");
    if (!value || !["none", "registry", "local"].includes(value.kind))
      return { kind: "none" };
    providerOrigin(value);
    return value;
  } catch {
    return { kind: "none" };
  }
}

export function ProviderOptions({
  settings,
  onSave,
}: {
  settings: ProviderSettings;
  onSave: (settings: ProviderSettings) => void;
}) {
  const [kind, setKind] = useState(settings.kind);
  const [url, setUrl] = useState(settings.kind === "none" ? "" : settings.url);
  const [token, setToken] = useState(
    settings.kind === "local" ? settings.token : "",
  );
  const [message, setMessage] = useState("");
  const [checking, setChecking] = useState(false);
  async function save() {
    try {
      const next: ProviderSettings =
        kind === "none"
          ? { kind }
          : kind === "registry"
            ? { kind, url: url.trim() }
            : { kind, url: url.trim(), token: token.trim() };
      const origin = providerOrigin(next);
      // Keep the permission request in this explicit user gesture.
      if (
        origin &&
        isExtension &&
        !(await chrome.permissions.request({ origins: [`${origin}/*`] }))
      )
        throw Error("Source access was declined.");
      if (isExtension) await chrome.storage.local.set({ [key]: next });
      else localStorage.setItem(key, JSON.stringify(next));
      onSave(next);
      setMessage("Saved. Choose Analyze capture to request a reading.");
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  return (
    <section
      className="options-section provider-options"
      aria-labelledby="provider-title"
    >
      <h3 id="provider-title">Analysis source</h3>
      <label>
        Provider
        <select
          value={kind}
          onChange={(e) => {
            const next = e.target.value as ProviderSettings["kind"];
            setKind(next);
            setUrl(next === "local" ? "http://127.0.0.1:8765" : "");
            setMessage("");
          }}
        >
          <option value="none">None</option>
          <option value="registry">Public registry</option>
          <option value="local">Local companion</option>
        </select>
      </label>
      {kind !== "none" && (
        <label>
          Source URL
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder={
              kind === "local"
                ? "http://127.0.0.1:8765"
                : "https://example.org/readings/"
            }
          />
        </label>
      )}
      {kind === "local" && (
        <label>
          Companion token
          <input
            type="password"
            autoComplete="off"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            spellCheck={false}
          />
        </label>
      )}
      <p className="muted">
        {kind === "local"
          ? "Analyze capture sends the captured text and selected context to your local companion. The token stays in this browser and is excluded from exported readings."
          : kind === "registry"
            ? "A lookup sends a four-character identifier hash prefix, followed by the full hash and revision when fetching a matching reading. No captured text or context is uploaded."
            : "Analysis is off. You can still import readings and explore the example."}
      </p>
      <button className="secondary-button" onClick={() => void save()}>
        Save analysis source
      </button>
      {settings.kind === "local" && (
        <button
          className="secondary-button"
          disabled={checking}
          onClick={async () => {
            setChecking(true);
            try {
              const health = await checkCompanion(settings);
              setMessage(
                `Connected to engine ${health.engineVersion}. ${health.historyAvailable.includes("wikipedia") ? "Wikipedia history is available." : "History analysis is not enabled."} ${health.admittedModules.length ? `${health.admittedModules.length} admitted modules.` : "Observed evidence only; inference modules await validation."}`,
              );
            } catch {
              setMessage(
                "Connection failed. Start Practice ToMpathy.cmd, connect there, then reopen this panel. Check the saved URL and token if using a separate companion.",
              );
            } finally {
              setChecking(false);
            }
          }}
        >
          {checking ? "Checking connection…" : "Check saved connection"}
        </button>
      )}
      {message && <p role="status">{message}</p>}
    </section>
  );
}
