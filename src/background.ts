import { companionRelay } from "./companion-relay";

chrome.sidePanel
  // Chrome's automatic panel toggle bypasses onClicked and does not grant
  // activeTab. Use the action event so ordinary-page capture has permission.
  .setPanelBehavior({ openPanelOnActionClick: false })
  .catch(() => {});
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return;
  // Keep this before any await to retain the action's user gesture.
  void chrome.sidePanel.open({ tabId: tab.id }).catch(console.error);
  await chrome.storage.session.set({ invokedTab: tab.id });
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"],
    });
  } catch {}
  void chrome.runtime
    .sendMessage({ type: "TOMPATHY_INVOKED", tabId: tab.id })
    .catch(() => {});
});
chrome.runtime.onConnect.addListener((port) => {
  if (companionRelay(port)) return;
  if (port.name !== "tompathy-panel") return;
  let tabId: number | undefined;
  port.onMessage.addListener((m) => {
    if (m.type === "TRACK") tabId = m.tabId;
  });
  port.onDisconnect.addListener(() => {
    if (tabId) {
      void chrome.tabs
        .sendMessage(tabId, { type: "TOMPATHY_CLEANUP" })
        .catch(() => {});
      void chrome.runtime
        .sendMessage({ type: "TOMPATHY_CLEANUP", targetTabId: tabId })
        .catch(() => {});
    }
  });
});
