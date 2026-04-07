/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";

import type { LayerMetadata } from "../types";

export type SetLayerFiltersParams<T> = {
  layerId: string;
  filters: T;
};

export function makeSetLayerFilters({
  map,
  baseUrl,
}: {
  map: MapLibreMap;
  baseUrl: URL;
}) {
  /**
   * Update map data of the selected layer based on the provided filters.
   *
   * @template T - The type of the filters object.
   * @param layerId Name of the layer to set filtered data.
   * @param filter Serializable configuration to provide to the endpoint
   *
   * @example
   * function filterByForest(selection: string){
   *   mapApiRef.current.setLayerFilters({
   *     layerId: "my-layer-id",
   *     filters: {
   *       op: "=",
   *       args: [{  property: "for" }, selection],
   *     }
   *   };
   * }
   */
  async function setLayerFilters<T>({
    layerId,
    filters,
  }: SetLayerFiltersParams<T>) {
    // Retrieve layer configuration
    const layer = map.getLayer(layerId);
    if (layer === undefined) {
      throw new Error(`[FILTERS] Layer ${layerId} doesn't exist.`);
    }

    // Retrieve dataUrl froom layer configuration
    const schema = (layer.metadata as LayerMetadata).schema;
    if (!schema) {
      throw new Error(`[FILTERS] Layer ${layer.id} can't be filtered.`);
    }
    const dataUrl = new URL(layerId, baseUrl).toString();

    // Fetch data based on filters
    const res = await fetch(dataUrl, {
      body: JSON.stringify(filters),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    const data = await res.json();

    console.log(`[FILTERS] Data fetched for layer ${layerId} with filters ${JSON.stringify(filters)}:`, data);
    // Update map internal state data
    const source = map.getSource(layer?.source) as GeoJSONSource;
    source?.setData(data);
  }

  return setLayerFilters;
}
