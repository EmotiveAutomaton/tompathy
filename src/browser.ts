import { makeArtifact, type Artifact, type Packet } from "./core/model";
export const isExtension =
  typeof chrome !== "undefined" && !!chrome.runtime?.id;
export async function capturePage(): Promise<{
  artifact: Artifact;
  tabId: number;
}> {
  if (!isExtension)
    throw Error("Open the installed extension on a page, or paste text below.");
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id)
    throw Error(
      "No active page. Open a text page, then click ToMpathy in the toolbar.",
    );
  try {
    let result;
    try {
      result = await chrome.runtime.sendMessage({
        type: "TOMPATHY_CAPTURE",
        targetTabId: tab.id,
      });
    } catch {}
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
    return { artifact: result.artifact, tabId: tab.id };
  } catch (e) {
    throw Error(
      `This page cannot be captured yet. Click ToMpathy’s toolbar icon on an ordinary text page, or paste text. ${e instanceof Error && e.message.startsWith("No readable") ? e.message : ""}`,
    );
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
    if (artifact.source.startsWith(chrome.runtime.getURL("")))
      await chrome.runtime.sendMessage(message);
    else await chrome.tabs.sendMessage(tabId, message);
  } catch {}
}
export async function markPage(
  tabId: number | null,
  artifact: Artifact | null,
  packet: Packet | null,
) {
  await pageCommand(tabId, artifact, "TOMPATHY_MARK", {
    estimates: packet?.estimates ?? [],
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
export async function writeSession(value: unknown) {
  if (isExtension) await chrome.storage.session.set({ reading: value });
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
