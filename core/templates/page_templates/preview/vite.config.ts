import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@tokens": resolve(__dirname, "src/tokens"),
      "@grid": resolve(__dirname, "src/grid"),
      "@primitives": resolve(__dirname, "src/primitives"),
      "@pages": resolve(__dirname, "src/pages"),
    },
  },
  server: {
    port: 5180,
    strictPort: true,
  },
  build: {
    target: "es2022",
    sourcemap: true,
    outDir: "dist",
  },
});
