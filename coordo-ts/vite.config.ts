/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

import { defineConfig } from "vite";
import { copyFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = fileURLToPath(new URL(".", import.meta.url));
const maplibreWorkerFiles = [
  "maplibre-gl-worker.mjs",
  "maplibre-gl-shared.mjs",
];

export default defineConfig({
  plugins: [
    {
      name: "copy-maplibre-worker-files",
      async closeBundle() {
        await Promise.all(
          maplibreWorkerFiles.map((file) =>
            copyFile(
              resolve(
                projectRoot,
                "node_modules/maplibre-gl/dist",
                file,
              ),
              resolve(projectRoot, "dist", file),
            ),
          ),
        );
      },
    },
  ],
  build: {
    lib: {
      entry: "src/index.ts",
      name: "coordo",
      formats: ["es", "iife"],
    },
  },
});
