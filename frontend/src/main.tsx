import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "@react-pdf-viewer/core/lib/styles/index.css";
import "@react-pdf-viewer/default-layout/lib/styles/index.css";
import "./index.css";

createRoot(document.getElementById("root")!).render(<App />);
