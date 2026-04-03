/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

export const EVENTS = {
  LAYER_HIDE: (layerId: string) => `layer:${layerId}:hide`,
  LAYER_SHOW: (layerId: string) => `layer:${layerId}:show`,
  MAP_READY: "map:ready",
} as const;
