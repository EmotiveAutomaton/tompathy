import { createRoot } from "react-dom/client";
import { useState } from "react";
import { EssaySurface } from "./components/Essay";
import { isEssayPage, type EssayPage } from "./content/essays";
import "./styles.css";
import "./essay.css";

const params = new URLSearchParams(location.search);
const kind = params.get("section");
const theme = params.get("theme");
if (theme === "dark" || theme === "light")
  document.documentElement.dataset.theme = theme;
document.body.className = "essay-standalone";
const parentOrigin = params.get("parentOrigin");
const nonce = params.get("nonce");
const tellParent = (type: string, extra = {}) => {
  if (parent !== window && parentOrigin && nonce)
    parent.postMessage({ type, nonce, ...extra }, parentOrigin);
};
const close = () => tellParent("TOMPATHY_ESSAY_CLOSE");
function Reader({ initial }: { initial: EssayPage }) {
  const [page, setPage] = useState(initial);
  return (
    <EssaySurface
      kind={page}
      onClose={close}
      onNavigate={(next) => {
        setPage(next);
        tellParent("TOMPATHY_ESSAY_PAGE", { page: next });
      }}
      onLightboxChange={(open) =>
        tellParent("TOMPATHY_ESSAY_LIGHTBOX", { open })
      }
    />
  );
}
if (isEssayPage(kind)) {
  createRoot(document.getElementById("root")!).render(
    <Reader initial={kind} />,
  );
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      e.preventDefault();
      close();
    }
  });
  tellParent("TOMPATHY_ESSAY_READY");
}
