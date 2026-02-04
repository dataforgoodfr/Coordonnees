import { defineConfig } from "vite";

export default defineConfig({
  build: {
    lib: {
      entry: "index.ts",
      name: "coordo",
    },
    rollupOptions: {
      external: ["maplibre-gl"],
      output: {
        globals: {
          "maplibre-gl": "maplibregl",
        },
      },
    },
  },
});
