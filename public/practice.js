const button = document.getElementById("connect");
const status = document.getElementById("connection");
const follow = document.getElementById("follow");
const following = document.getElementById("following");
follow.addEventListener("click", async () => {
  try {
    if (
      !(await chrome.permissions.request({
        origins: ["https://*/*", "http://*/*"],
      }))
    )
      throw Error(
        "Page access was declined. Manual capture and paste text remain available.",
      );
    await chrome.storage.local.set({ "tompathy-follow-pages": true });
    following.textContent =
      "Follow pages is on. Open the panel once; it follows the active page. Turn this off in the reader menu.";
  } catch (error) {
    following.textContent = error.message;
  }
});
let setup;
function valid(value) {
  if (
    !value ||
    !/^http:\/\/127\.0\.0\.1:\d+$/.test(value.url) ||
    !/^[0-9a-f]{64}$/.test(value.token)
  )
    return false;
  const port = Number(new URL(value.url).port);
  return port > 0 && port < 65536;
}
async function load() {
  if (!globalThis.chrome?.runtime?.id) return;
  setup = (await chrome.storage.session.get("tompathy-practice-setup"))[
    "tompathy-practice-setup"
  ];
  button.disabled = !valid(setup);
  if (!button.disabled)
    status.textContent =
      "The local companion is ready to connect. This does not analyze a page.";
}
button.addEventListener("click", async () => {
  if (!valid(setup)) return;
  // Optional host access is requested only from this explicit user gesture.
  const permission = chrome.permissions.request({
    origins: [`${setup.url}/*`],
  });
  button.disabled = true;
  status.textContent =
    "Allow the local connection in Chrome’s permission prompt, if shown…";
  try {
    if (!(await permission)) throw Error("Local access was declined.");
    const response = await fetch(`${setup.url}/v1/health`, {
      headers: { Authorization: `Bearer ${setup.token}` },
      credentials: "omit",
      redirect: "error",
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok)
      throw Error(
        "The companion could not be reached. Restart the practice launcher.",
      );
    const health = await response.json();
    if (
      health.implementationHash !== setup.implementation ||
      !health.historyAvailable?.includes("wikipedia")
    )
      throw Error(
        "The running engine differs from this practice setup. Restart the launcher.",
      );
    await chrome.storage.local.set({
      "tompathy-provider": {
        kind: "local",
        url: setup.url,
        token: setup.token,
      },
    });
    status.textContent = `Connected to engine ${health.engineVersion}. ${health.previewAvailable ? "Research preview is available with labeled local guesses." : "Observed evidence is available."} ${health.admittedModules.length ? "Admitted modules are available." : "No production inference module is admitted."} Open an article to begin.`;
    button.querySelector("strong").textContent = "Reconnect local engine";
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});
if (globalThis.chrome?.storage) {
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === "session" && changes["tompathy-practice-setup"]) void load();
  });
  await load();
}
