import { createRoot } from "react-dom/client";
import "./styles.css";
import "./reader.css";
import { App, ExampleArticle } from "./App";
import { isExtension } from "./browser";
const example = isExtension && location.pathname.endsWith("example.html");
createRoot(document.getElementById("root")!).render(
  example ? (
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
