import { createRoot } from "react-dom/client";
import "./styles.css";
import "./reader.css";
import "./mind.css";
import { SavedPage } from "./components/SavedPage";
import { App, ExampleArticle } from "./App";
import { isExtension } from "./browser";
const example = isExtension && location.pathname.endsWith("example.html");
createRoot(document.getElementById("root")!).render(
  location.pathname.endsWith("snapshot.html") ? (
    <SavedPage />
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
if (example) void import("./content");
