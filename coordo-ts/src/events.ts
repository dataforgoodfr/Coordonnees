export const EVENTS = {
  LAYER_HIDE: (layerId: string) => `layer:${layerId}:hide`,
  LAYER_SHOW: (layerId: string) => `layer:${layerId}:show`,
  MAP_READY: "map:ready",
} as const;
