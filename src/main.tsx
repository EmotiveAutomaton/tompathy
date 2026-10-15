import { createRoot } from "react-dom/client";
import "./styles.css";
import "./reader.css";
import "./mind.css";
import "./reading.css";
import { attachReadingHelp } from "./reading-help";
import { SavedPage } from "./components/SavedPage";
import { App, ExampleArticle } from "./App";
import { ArtArticle } from "./components/ArtArticle";
import { isExtension } from "./browser";
const example = isExtension && location.pathname.endsWith("example.html");
const art = isExtension && location.pathname.endsWith("art.html");
createRoot(document.getElementById("root")!).render(
  location.pathname.endsWith("snapshot.html") ? (
    <SavedPage />
  ) : art ? (
    <ArtArticle />
  ) : example ? (
    <ExampleArticle />
  ) : (
    <App
      preview={
        !isExtension && !new URLSearchParams(location.search).has("panel")
      }
    />
  ),
);
if (example || art) void import("./content");
else if (!location.pathname.endsWith("snapshot.html")) attachReadingHelp();
