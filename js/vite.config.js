//import { resolve } from "path";
import { defineConfig } from "vite";

export default defineConfig({
  build: {
    lib: {
      entry: "index.js",
      name: "coordo",
    },
  },
});
