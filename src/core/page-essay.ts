import { isEssayPage, essayLabels } from "../content/essay-kind";

/** A public, packaged essay over the source, isolated from its CSS and capture. */
export function pageEssay() {
  let closeCurrent = () => {};
  return {
    close: () => closeCurrent(),
    open(kind: unknown, theme: unknown): Promise<boolean> {
      closeCurrent();
      if (!isEssayPage(kind)) return Promise.resolve(false);
      return new Promise((resolve) => {
        const prior = document.activeElement as HTMLElement | null;
        const host = document.createElement("div");
        host.dataset.tompathyUi = "essay";
        const shadow = host.attachShadow({ mode: "open" });
        const style = document.createElement("style");
        style.textContent = `:host{all:initial} dialog{box-sizing:border-box;position:fixed;margin:auto;width:calc(100vw - 48px);height:calc(100dvh - 48px);max-width:none;max-height:none;padding:0;border:1px solid #71857866;border-radius:16px;overflow:hidden;background:#fff;box-shadow:0 24px 90px #10261f40}dialog::backdrop{background:#10221c80;backdrop-filter:blur(2px)}dialog.image-open{width:100vw;height:100dvh;margin:0;border:0;border-radius:0;background:#000}dialog.image-open::backdrop{background:#000}iframe{display:block;border:0;width:100%;height:100%}`;
        const dialog = document.createElement("dialog");
        dialog.setAttribute("aria-label", essayLabels[kind]);
        const frame = document.createElement("iframe");
        frame.title = essayLabels[kind];
        const nonce = crypto.randomUUID();
        const extensionOrigin = chrome.runtime.getURL("").replace(/\/$/, "");
        const pageOrigin =
          location.protocol === "chrome-extension:"
            ? extensionOrigin
            : location.origin;
        const url = new URL(chrome.runtime.getURL("essay.html"));
        url.searchParams.set("section", kind);
        url.searchParams.set(
          "theme",
          theme === "dark" || theme === "light" ? theme : "system",
        );
        url.searchParams.set("nonce", nonce);
        url.searchParams.set("parentOrigin", pageOrigin);
        frame.src = url.href;
        let ready = false;
        const finish = () => {
          clearTimeout(timeout);
          window.removeEventListener("message", message);
          dialog.close();
          host.remove();
          if (prior?.isConnected) prior.focus({ preventScroll: true });
          if (!ready) resolve(false);
          closeCurrent = () => {};
        };
        const message = (event: MessageEvent) => {
          if (
            event.source !== frame.contentWindow ||
            event.origin !== extensionOrigin ||
            event.data?.nonce !== nonce
          )
            return;
          if (event.data.type === "TOMPATHY_ESSAY_READY") {
            ready = true;
            clearTimeout(timeout);
            resolve(true);
          }
          if (event.data.type === "TOMPATHY_ESSAY_CLOSE") finish();
          const nextPage: unknown = event.data.page;
          if (
            event.data.type === "TOMPATHY_ESSAY_PAGE" &&
            isEssayPage(nextPage)
          ) {
            dialog.setAttribute("aria-label", essayLabels[nextPage]);
            frame.title = essayLabels[nextPage];
          }
          if (
            event.data.type === "TOMPATHY_ESSAY_LIGHTBOX" &&
            typeof event.data.open === "boolean"
          ) {
            dialog.classList.toggle("image-open", event.data.open);
          }
        };
        const timeout = setTimeout(finish, 5000);
        window.addEventListener("message", message);
        closeCurrent = finish;
        let downOutside = false;
        const outside = (e: MouseEvent) => {
          const r = dialog.getBoundingClientRect();
          return (
            e.clientX < r.left ||
            e.clientX > r.right ||
            e.clientY < r.top ||
            e.clientY > r.bottom
          );
        };
        dialog.addEventListener("pointerdown", (e) => {
          downOutside = outside(e);
        });
        dialog.addEventListener("click", (e) => {
          if (downOutside && outside(e)) finish();
        });
        dialog.addEventListener("cancel", (e) => {
          e.preventDefault();
          finish();
        });
        dialog.append(frame);
        shadow.append(style, dialog);
        document.documentElement.append(host);
        try {
          dialog.showModal();
        } catch {
          finish();
        }
      });
    },
  };
}
