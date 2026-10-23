/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

import type { Map as MapLibreMap } from "maplibre-gl";

import type { LayerMetadata } from "../types";
import {
  type CqlExpression,
  getCqlProperties,
  type LayerSchemas,
  type RawCqlFilter,
  type Where,
  whereToCql,
} from "./cql";
import { setSourceData } from "./source-filter";

// Enough to read a backend error message without dumping a whole HTML page.
const MAX_ERROR_BODY_LENGTH = 300;

export type LayerId<TLayers extends LayerSchemas> = Extract<
  keyof TLayers,
  string
>;

/**
 * Either a {@link Where} object or a CQL2 filter (builder output or raw JSON),
 * not both. `null` or `undefined` filters restore the unfiltered data.
 */
export type SetLayerFiltersParams<
  TLayers extends LayerSchemas = LayerSchemas,
  L extends LayerId<TLayers> = LayerId<TLayers>,
> = { layerId: L } & (
  | { filters?: never; where: Where<TLayers[L]> }
  | { filters: CqlExpression | RawCqlFilter | null | undefined; where?: never }
);

/**
 * Throw when the filter refers to a property the layer's resource doesn't have.
 * The backend would otherwise answer with an empty layer, which looks exactly
 * like "no data".
 */
function assertKnownProperties(
  layerId: string,
  metadata: LayerMetadata | undefined,
  filter: unknown,
) {
  const fields = metadata?.resource?.schema?.fields;
  // Only datapackage layers describe their resource: nothing to check against.
  if (!fields) {
    return;
  }

  const available = fields.map((field) => field.name);
  const unknown = getCqlProperties(filter).filter(
    (property) => !available.includes(property),
  );
  if (unknown.length > 0) {
    throw new Error(
      `[FILTERS] Unknown ${unknown.length > 1 ? "properties" : "property"} ${unknown.map((property) => `"${property}"`).join(", ")} on layer "${layerId}". Filters use the raw resource column names. Available: ${available.join(", ")}.`,
    );
  }
}

async function getFailureMessage(res: Response, layerId: string) {
  const body = await res.text().catch(() => "");
  const details = body ? ` - ${body.slice(0, MAX_ERROR_BODY_LENGTH)}` : "";
  return `[FILTERS] Fetching the filtered data of layer "${layerId}" failed: ${res.status} ${res.statusText}${details}`;
}

export function makeLayerFilters<TLayers extends LayerSchemas>({
  map,
  baseUrl,
  headers,
}: {
  map: MapLibreMap;
  baseUrl: URL;
  headers?: Record<string, string>;
}) {
  // One request in flight per layer: a newer call supersedes the previous one.
  const pendingRequests = new Map<string, AbortController>();

  /**
   * Replace the data of a layer with the backend's data for these filters.
   *
   * Filters are applied by the backend to the layer's resource, **before** it is
   * grouped or aggregated: each feature is recomputed from the matching rows
   * only. Properties are therefore the raw resource column names, not the
   * aliases of the layer `columns`.
   *
   * The client-side filter set with `setSourceFilter` is kept.
   *
   * @returns A promise resolved once the new data is on the map. It rejects
   *   - when the filter refers to an unknown property (nothing is fetched);
   *   - when the backend answers with an error (the current data is kept);
   *   - with an `AbortError` when a newer call for the same layer supersedes it.
   *
   * @example
   * mapApi.setLayerFilters({
   *   layerId: "enquete",
   *   where: {
   *     coh: { between: ["2022", "2023"] },
   *     typ: { in: ["1", "2"] },
   *   },
   * });
   *
   * @example
   * mapApi.setLayerFilters({
   *   filters: cql.or(cql.eq("sex", "2"), cql.lt("age", "2")),
   *   layerId: "enquete",
   * });
   */
  async function setLayerFilters<L extends LayerId<TLayers>>(
    params: SetLayerFiltersParams<TLayers, L>,
  ) {
    const { layerId } = params;
    const layer = map.getLayer(layerId);
    if (layer === undefined) {
      throw new Error(`[FILTERS] Layer ${layerId} doesn't exist.`);
    }

    const filter =
      params.where === undefined ? params.filters : whereToCql(params.where);
    assertKnownProperties(
      layerId,
      layer.metadata as LayerMetadata | undefined,
      filter,
    );

    pendingRequests.get(layerId)?.abort();
    const controller = new AbortController();
    pendingRequests.set(layerId, controller);

    try {
      const res = await fetch(new URL(layerId, baseUrl).toString(), {
        // An empty object means "no filter" to the backend.
        body: JSON.stringify(filter ?? {}),
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        method: "POST",
        signal: controller.signal,
      });
      if (!res.ok) {
        throw new Error(await getFailureMessage(res, layerId));
      }
      const data = await res.json();
      // The response may have been read just before a newer call came in.
      controller.signal.throwIfAborted();

      // Update map internal state data, keeping any client-side source filter
      setSourceData({ data, map, sourceId: layer.source });
    } finally {
      if (pendingRequests.get(layerId) === controller) {
        pendingRequests.delete(layerId);
      }
    }
  }

  /** Restore the unfiltered data of a layer. Same promise as `setLayerFilters`. */
  function clearLayerFilters(layerId: LayerId<TLayers>) {
    return setLayerFilters({ filters: null, layerId });
  }

  return { clearLayerFilters, setLayerFilters };
}
