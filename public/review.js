const label = document.getElementById("build");
try {
  if (!globalThis.chrome?.runtime?.id) {
    label.textContent = "Preview only · use Review ToMpathy.cmd for Chrome";
  } else {
    const info = await (await fetch("build-info.json")).json();
    label.textContent = `Installed · ${chrome.runtime.getManifest().version_name ?? chrome.runtime.getManifest().version} · build ${info.fingerprint}`;
  }
} catch {
  label.textContent =
    "Build information unavailable · rerun Review ToMpathy.cmd";
}
