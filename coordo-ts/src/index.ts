import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import "./index.css";

import { LAYER_VISIBILITY } from "./layers/controls";
import { makeSetLayerFilters } from "./layers/filters";
import { makeSetLayerPopup } from "./layers/popup";
import { addStyleDataListener } from "./map/style-data";

const DEFAULT_MAP_OPTIONS: Partial<maplibregl.MapOptions> = {
  center: [0, 0],
  zoom: 1,
};

export function createMap(
  target: string | HTMLElement,
  styleUrl = "https://demotiles.maplibre.org/globe.json",
  options?: Partial<maplibregl.MapOptions>,
) {
  const el =
    typeof target === "string"
      ? (document.querySelector(target) as HTMLElement)
      : target;

  if (!el) {
    throw new Error("[CREATE] Map target not found");
  }

  const baseUrl = new URL(".", new URL(styleUrl, window.location.href));
  console.log("baseUrl", baseUrl);

  const mergedOptions = { ...DEFAULT_MAP_OPTIONS, ...options };

  const map = new maplibregl.Map({
    center: mergedOptions.center,
    container: el,
    style: styleUrl,
    zoom: mergedOptions.zoom,
  });

  function hideLayer(layerId: string) {
    map.setLayoutProperty(layerId, "visibility", LAYER_VISIBILITY.NONE);
  }

  function showLayer(layerId: string) {
    map.setLayoutProperty(layerId, "visibility", LAYER_VISIBILITY.VISIBLE);
  }

  function getLayerMetadata(layerId: string) {
    return map.getLayer(layerId)?.metadata;
  }

  function getZoom() {
    return map.getZoom();
  }

  function getCenter() {
    return map.getCenter().toArray();
  }

  const setLayerFilters = makeSetLayerFilters({ baseUrl, map });

  const setLayerPopup = makeSetLayerPopup({ map });

  function addEventListener<T extends keyof maplibregl.MapEventType>(
    type: T,
    listener: (ev: maplibregl.MapEventType[T] & Object) => void,
  ): maplibregl.Subscription {
    return map.on(type, listener);
  }

  function init() {
    el.dispatchEvent(new CustomEvent("map:ready"));
  }

  addStyleDataListener({
    map,
    onSuccess: init,
    setLayerPopup,
  });

  return {
    addEventListener,
    getCenter,
    getLayerMetadata,
    getZoom,
    hideLayer,
    mapInstance: map,
    setLayerFilters,
    setLayerPopup,
    showLayer,
  };
}
