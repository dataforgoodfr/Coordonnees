/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

import type {
  FilterSpecification,
  GeoJSONSource,
  Map as MapLibreMap,
} from "maplibre-gl";

// The unfiltered data of every source we have filtered, so a filter can be
// widened again. Keyed by map instance so a remount starts clean.
const ORIGINAL_DATA = new WeakMap<
  MapLibreMap,
  Map<string, GeoJSON.GeoJSON | string>
>();

// Serialized filter currently applied per source, to skip no-op updates.
const CURRENT_FILTER = new WeakMap<MapLibreMap, Map<string, string>>();

function getOrCreate<V>(
  store: WeakMap<MapLibreMap, Map<string, V>>,
  map: MapLibreMap,
) {
  let bySource = store.get(map);
  if (!bySource) {
    bySource = new Map();
    store.set(map, bySource);
  }
  return bySource;
}

function getGeoJSONSource(map: MapLibreMap, sourceId: string) {
  const source = map.getSource(sourceId);
  if (source?.type !== "geojson") {
    return undefined;
  }
  return source as GeoJSONSource;
}

/**
 * Snapshot the source data the first time we touch it: before any filter is
 * applied, `serialize().data` is still the untouched data from the style.
 */
function getOriginalData(
  map: MapLibreMap,
  sourceId: string,
  source: GeoJSONSource,
) {
  const dataBySource = getOrCreate(ORIGINAL_DATA, map);
  if (!dataBySource.has(sourceId)) {
    dataBySource.set(sourceId, source.serialize().data);
  }
  return dataBySource.get(sourceId) as GeoJSON.GeoJSON | string;
}

/**
 * Filter the data behind a layer *before* it is clustered.
 *
 * `map.setFilter()` is a render-time filter: on a clustered source the points
 * are hidden, but cluster bubbles keep counting them, since supercluster
 * indexes the whole source. This filter is instead applied by the MapLibre
 * worker when it loads the source (the GeoJSON source `filter` option), so the
 * cluster index — hence the counts — only sees matching features.
 *
 * Each change re-sends the data to the worker and rebuilds the index, so prefer
 * `setFilter` for layers whose source is not clustered.
 *
 * @param layerId Layer whose source gets filtered (every layer bound to that
 *   source is affected).
 * @param filter MapLibre filter expression, or `null` to show everything.
 *
 * @example
 * setSourceFilter({
 *   map,
 *   layerId: "my-layer-id",
 *   filter: ["in", ["get", "project"], ["literal", ["A", "B"]]],
 * });
 */
export function setSourceFilter({
  map,
  layerId,
  filter,
}: {
  map: MapLibreMap;
  layerId: string;
  filter: FilterSpecification | null;
}) {
  const layer = map.getLayer(layerId);
  if (layer === undefined) {
    throw new Error(`[FILTERS] Layer ${layerId} doesn't exist.`);
  }

  const source = getGeoJSONSource(map, layer.source);
  if (!source) {
    console.warn(
      `[FILTERS] Source of layer ${layerId} is not a GeoJSON source, source filter ignored.`,
    );
    return;
  }

  const filterBySource = getOrCreate(CURRENT_FILTER, map);
  const serialized = JSON.stringify(filter);
  // Unset counts as `null`: skips the first, filterless refresh on load.
  if ((filterBySource.get(layer.source) ?? "null") === serialized) {
    return;
  }

  const data = getOriginalData(map, layer.source, source);
  filterBySource.set(layer.source, serialized);

  // Read by the worker on the next data load, before the cluster index is built.
  // The worker only takes expressions: map the boolean shorthands onto them.
  source.workerOptions.filter = Array.isArray(filter)
    ? filter
    : filter === false
      ? ["literal", false]
      : undefined;
  source.setData(data);
}

/**
 * Replace a source's data while keeping its source filter: the new data
 * becomes the unfiltered reference, and the worker re-applies the current
 * `workerOptions.filter` on load.
 */
export function setSourceData({
  map,
  sourceId,
  data,
}: {
  map: MapLibreMap;
  sourceId: string;
  data: GeoJSON.GeoJSON;
}) {
  const source = getGeoJSONSource(map, sourceId);
  if (!source) {
    return;
  }

  getOrCreate(ORIGINAL_DATA, map).set(sourceId, data);
  source.setData(data);
}
