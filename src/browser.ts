import {
  makeArtifact,
  type Artifact,
  type Packet,
  type Session,
} from "./core/model";
export const isExtension =
  typeof chrome !== "undefined" && !!chrome.runtime?.id;
/** Expected browser access states are guidance, not failed analysis. */
export class PageCaptureUnavailable extends Error {
  constructor(
    message: string,
    readonly kind: "empty" | "access" | "loading" = "access",
  ) {
    super(message);
  }
}
export const followPageOrigins = ["https://*/*", "http://*/*"];
export async function readFollowPages(): Promise<boolean> {
  return (
    isExtension &&
    (await chrome.storage.local.get("tompathy-follow-pages"))[
      "tompathy-follow-pages"
    ] === true
  );
}
export async function saveFollowPages(enabled: boolean) {
  if (!isExtension) return;
  // Chrome requires a gesture for this persistent, optional site grant.
  if (
    enabled &&
    !(await chrome.permissions.request({ origins: followPageOrigins }))
  )
    throw Error(
      "Page access was declined. You can still paste text or open the example.",
    );
  await chrome.storage.local.set({ "tompathy-follow-pages": enabled });
}
export async function capturePage(): Promise<{
  artifact: Artifact;
  tabId: number;
  restored?: Session;
  contextSources?: Session["contextSources"];
  repositoryLinks?: Session["repositoryLinks"];
}> {
  if (!isExtension)
    throw Error("Open the installed extension on a page, or paste text below.");
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id)
    throw new PageCaptureUnavailable(
      "Open a page with text, or paste a piece of writing.",
      "empty",
    );
  if (tab.url === "about:blank" || tab.url === "chrome://newtab/")
    throw new PageCaptureUnavailable(
      "Open a page with text, or paste a piece of writing.",
      "empty",
    );
  if (tab.status === "loading")
    throw new PageCaptureUnavailable(
      "Waiting for the page to finish loading…",
      "loading",
    );
  try {
    let result;
    try {
      result = await chrome.runtime.sendMessage({
        type: "TOMPATHY_CAPTURE",
        targetTabId: tab.id,
      });
    } catch {}
    if (result?.error) throw Error(result.error);
    if (!result?.artifact) {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["content.js"],
      });
      result = await chrome.tabs.sendMessage(tab.id, {
        type: "TOMPATHY_CAPTURE",
      });
    }
    if (result.error) throw Error(result.error);
    if (!result.artifact) throw Error("The page adapter returned no capture.");
    return {
      artifact: result.artifact,
      tabId: tab.id,
      restored: result.restored,
      contextSources: result.contextSources,
      repositoryLinks: result.repositoryLinks,
    };
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    // Handle known blank URLs when Chrome includes them. Without tabs access,
    // Chrome can hide both the URL and error details; keep that access failure
    // distinct from an inspected webpage that genuinely contains no text.
    if (/about:blank|chrome:\/\/newtab\//i.test(message))
      throw new PageCaptureUnavailable(
        "Open a page with text, or paste a piece of writing.",
        "empty",
      );
    if (/No readable/i.test(message))
      throw new PageCaptureUnavailable(
        "There is no readable text on this page. Try another page or paste a piece of writing.",
        "empty",
      );
    if (
      /Cannot access|Missing host permission|not allowed to access|extensions gallery cannot be scripted|cannot be scripted/i.test(
        message,
      )
    )
      throw new PageCaptureUnavailable(
        "Sorry, this page could not be read. Enable Follow pages to allow reading across websites. Chrome’s internal pages and protected sites cannot be read, even with access enabled.",
      );
    throw Error(`The page could not be read. ${message}`);
  }
}
export async function captureSelection(): Promise<Artifact> {
  if (!isExtension)
    throw Error("Use the installed extension to read a selection from a page.");
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw Error("Open a text page first.");
  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      const selection = getSelection();
      const blocked =
        'input,textarea,[contenteditable]:not([contenteditable="false"]),[hidden],[aria-hidden="true"]';
      if (
        !selection ||
        selection.isCollapsed ||
        selection.anchorNode?.parentElement?.closest(blocked) ||
        selection.focusNode?.parentElement?.closest(blocked)
      )
        return null;
      const copy = selection.getRangeAt(0).cloneContents();
      copy.querySelectorAll(blocked).forEach((n) => n.remove());
      return {
        text: copy.textContent ?? "",
        source: location.href,
        title: `Selection from ${document.title}`,
      };
    },
  });
  const selected = results[0]?.result;
  if (!selected?.text.trim())
    throw Error(
      "Select readable page text first. Editable fields are excluded.",
    );
  if (selected.text.length > 300000)
    throw Error("Select fewer than 300,000 characters.");
  return makeArtifact([selected.text], selected.source, selected.title);
}
export async function pageCommand(
  tabId: number | null,
  artifact: Artifact | null,
  type: string,
  data: object = {},
) {
  if (!isExtension || tabId === null || !artifact) return;
  const message = {
    type,
    targetTabId: tabId,
    documentId: artifact.id,
    revision: artifact.revision,
    ...data,
  };
  try {
    try {
      await chrome.tabs.sendMessage(tabId, message);
    } catch {
      await chrome.runtime.sendMessage(message);
    }
  } catch {}
}
export async function openPageEssay(
  tabId: number | null,
  artifact: Artifact | null,
  kind: "goals" | "process" | "values" | "bibliography",
  theme: string,
): Promise<boolean> {
  if (!isExtension || tabId === null || !artifact) return false;
  const message = { type: "TOMPATHY_OPEN_ESSAY", targetTabId: tabId,
    documentId: artifact.id, revision: artifact.revision, kind, theme };
  try {
    let result;
    try { result = await chrome.tabs.sendMessage(tabId, message); }
    catch { result = await chrome.runtime.sendMessage(message); }
    return result?.ok === true;
  } catch { return false; }
}
export async function markPage(
  tabId: number | null,
  artifact: Artifact | null,
  packet: Packet | null,
  maker?: string,
) {
  await pageCommand(tabId, artifact, "TOMPATHY_MARK", {
    estimates: packet?.estimates ?? [],
    ghostReadings: packet?.ghostReadings,
    evidence: packet?.evidence,
    origin: packet?.origin,
    maker,
    documentContribution: packet?.documentContribution,
  });
}
export async function readSession() {
  if (isExtension) return (await chrome.storage.session.get("reading")).reading;
  try {
    return JSON.parse(sessionStorage.getItem("tompathy-session") ?? "null");
  } catch {
    return null;
  }
}
export async function writeSession(value: Session) {
  if (isExtension)
    await chrome.storage.session.set({
      reading: value,
      ...(value.savedPageId
        ? { [`snapshot:${value.savedPageId}`]: value }
        : {}),
    });
  else sessionStorage.setItem("tompathy-session", JSON.stringify(value));
}
export async function readTheme(): Promise<string> {
  if (isExtension) {
    const t = (await chrome.storage.local.get("theme")).theme;
    return typeof t === "string" ? t : "system";
  }
  return localStorage.getItem("tompathy-theme") ?? "system";
}
export async function writeTheme(theme: string) {
  if (isExtension) await chrome.storage.local.set({ theme });
  else localStorage.setItem("tompathy-theme", theme);
}
export function download(name: string, data: unknown) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
