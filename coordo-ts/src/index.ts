/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

export type { PopupOptions } from "maplibre-gl";

export { EVENTS } from "./events";
export { getClusterLayerIds } from "./layers/cluster";
export {
  LAYER_CONTROL_ELEMENTS,
  type LayerControlRenderAnchor,
  type LayerControlRenderLayerRow,
} from "./layers/controls";
export {
  type CqlBuilder,
  type CqlExpression,
  type CqlProperty,
  type CqlScalar,
  cql,
  createCql,
  type LayerProperties,
  type LayerSchemas,
  type RawCqlFilter,
  type Where,
  type WhereCondition,
  whereToCql,
} from "./layers/cql";
export type { LayerId, SetLayerFiltersParams } from "./layers/filters";
export { setSourceFilter } from "./layers/source-filter";
export { getLayerSymbolId } from "./layers/symbol";
export { type CreateMapOptions, createMap } from "./map/map";
export type {
  FrictionlessField,
  FrictionlessSchema,
  LayerMetadata,
} from "./types";
