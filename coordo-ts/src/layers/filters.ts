import type { Map as MapLibreMap, GeoJSONSource } from "maplibre-gl";
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
  baseUrl: string;
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
    let dataUrl = (layer.metadata as LayerMetadata).url;
    if (!dataUrl) {
      throw new Error(`[FILTERS] Layer ${layer.id} can't be filtered.`);
    }
    if (!dataUrl.startsWith("http")) {
      dataUrl = new URL(dataUrl, baseUrl).toString();
    }

    // Fetch data based on filters
    const res = await fetch(dataUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(filters),
    });
    const data = await res.json();

    // Update map internal state data
    const source = map.getSource(layer?.source) as GeoJSONSource;
    source?.setData(data);
  }

  return setLayerFilters;
}
