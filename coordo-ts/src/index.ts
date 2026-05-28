/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

export type { PopupOptions } from "maplibre-gl";

export { EVENTS } from "./events";
export {
  LAYER_CONTROL_ELEMENTS,
  type LayerControlRenderAnchor,
  type LayerControlRenderLayerRow,
} from "./layers/controls";
export { getLayerSymbolId } from "./layers/symbol";
export { type CreateMapOptions, createMap } from "./map/map";
export type {
  FrictionlessField,
  FrictionlessSchema,
  LayerMetadata,
} from "./types";
