import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import tailwindcss from "@tailwindcss/vite"
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    hmr: {
      overlay: false,
    },
  },
  plugins: [react(), tailwindcss(),mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: [
      { find: "@", replacement: path.resolve(__dirname, "./src") },
      {
        // Exact-match only — prevents sub-path imports like
        // "pdfjs-dist/legacy/build/pdf.worker.min.js" from being mangled.
        find: /^pdfjs-dist$/,
        replacement: path.resolve(
          __dirname,
          "node_modules/pdfjs-dist/legacy/build/pdf.js",
        ),
      },
    ],
  },
  optimizeDeps: {
    include: ["pdfjs-dist"],
  },
}));
