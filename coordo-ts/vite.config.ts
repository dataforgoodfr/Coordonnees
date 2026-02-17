import { defineConfig } from "vite";

export default defineConfig({
  build: {
    lib: {
      entry: "index.ts",
      name: "coordo",
      formats: ["es", "iife"],
    },
  },
});
