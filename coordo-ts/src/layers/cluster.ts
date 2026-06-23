/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

import type {
  FilterSpecification,
  GeoJSONSource,
  Map as MapLibreMap,
  PropertyValueSpecification,
  StyleSpecification,
} from "maplibre-gl";

// Hardcoded cluster styling for the starter iteration.
// (Later this can be driven by layer metadata from coordo-py.)
const CLUSTER_COLORS = ["#51bbd6", "#f1f075", "#f28cb1"];
const CLUSTER_RADII = [20, 30, 40];
const CLUSTER_STEPS = [100, 750]; // point_count thresholds between the 3 buckets

const IS_CLUSTER: FilterSpecification = ["has", "point_count"];
const IS_NOT_CLUSTER: FilterSpecification = ["!", ["has", "point_count"]];

function getClusterLayerIds(sourceId: string) {
  return {
    circle: `${sourceId}-clusters`,
    count: `${sourceId}-cluster-count`,
  };
}

/**
 * Build a MapLibre `step` expression keyed on point_count:
 *   ["step", ["get","point_count"], v0, s0, v1, s1, v2]
 */
function stepByPointCount<T extends number | string>(
  values: T[],
  steps: number[],
): PropertyValueSpecification<T> {
  const expr: unknown[] = ["step", ["get", "point_count"], values[0]];
  steps.forEach((step, i) => {
    expr.push(step, values[i + 1]);
  });
  return expr as unknown as PropertyValueSpecification<T>;
}

/**
 * Keep existing layers bound to a clustered source from rendering on top of
 * cluster features
 */
function excludeClustersFromLayer(map: MapLibreMap, layerId: string) {
  const existing = map.getFilter(layerId);
  const next = (
    existing ? ["all", IS_NOT_CLUSTER, existing] : IS_NOT_CLUSTER
  ) as FilterSpecification;
  map.setFilter(layerId, next);
}

function addClusterLayers(map: MapLibreMap, sourceId: string) {
  const { circle, count } = getClusterLayerIds(sourceId);

  if (!map.getLayer(circle)) {
    map.addLayer({
      filter: IS_CLUSTER,
      id: circle,
      paint: {
        "circle-color": stepByPointCount(CLUSTER_COLORS, CLUSTER_STEPS),
        "circle-radius": stepByPointCount(CLUSTER_RADII, CLUSTER_STEPS),
      },
      source: sourceId,
      type: "circle",
    });
  }

  if (!map.getLayer(count)) {
    map.addLayer({
      filter: IS_CLUSTER,
      id: count,
      layout: {
        "text-field": "{point_count_abbreviated}",
        "text-font": ["Noto Sans Regular"],
        "text-size": 12,
      },
      source: sourceId,
      type: "symbol",
    });
  }
}

function wireClusterInteractions(map: MapLibreMap, sourceId: string) {
  const { circle } = getClusterLayerIds(sourceId);

  // Click a cluster -> ease in to the zoom level where it expands.
  map.on("click", circle, async (e) => {
    const features = map.queryRenderedFeatures(e.point, { layers: [circle] });
    const feature = features[0];
    const clusterId = feature?.properties?.cluster_id;
    if (clusterId === undefined || feature?.geometry.type !== "Point") {
      return;
    }
    const source = map.getSource(sourceId) as GeoJSONSource;
    const zoom = await source.getClusterExpansionZoom(clusterId);
    map.easeTo({
      center: feature.geometry.coordinates as [number, number],
      zoom,
    });
  });

  map.on("mouseenter", circle, () => {
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", circle, () => {
    map.getCanvas().style.cursor = "";
  });
}

/**
 * For every GeoJSON source declared with `cluster: true`, render the cluster
 * bubble + count layers, keep other layers off the cluster features, and wire
 * click-to-zoom. Driven entirely by the source flag emitted by coordo-py.
 */
export function setupClustering({
  map,
  style,
}: {
  map: MapLibreMap;
  style: StyleSpecification;
}) {
  const sources = style.sources ?? {};
  const layers = style.layers ?? [];

  Object.entries(sources).forEach(([sourceId, source]) => {
    if (source.type !== "geojson" || !source.cluster) {
      return;
    }

    layers
      .filter((layer) => "source" in layer && layer.source === sourceId)
      .forEach((layer) => {
        excludeClustersFromLayer(map, layer.id);
      });

    addClusterLayers(map, sourceId);
    wireClusterInteractions(map, sourceId);
  });
}
