import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "./index.css";
import { makeSetLayerPopup } from "./layers/popup";
import { makeSetLayerFilters } from "./layers/filters";
import { addStyleDataListener } from "./map/style-data";

const DEFAULT_MAP_OPTIONS: Partial<maplibregl.MapOptions> = {
  zoom: 1,
  center: [0, 0],
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

  if (!el) throw new Error("Map target not found");
  const baseUrl = styleUrl.startsWith("http")
    ? new URL(styleUrl).origin
    : window.location.href;

  const mergedOptions = { ...DEFAULT_MAP_OPTIONS, ...options };

  const map = new maplibregl.Map({
    container: el,
    style: styleUrl,
    center: mergedOptions.center,
    zoom: mergedOptions.zoom,
  });

  function hideLayer(layerId: string) {
    map.setLayoutProperty(layerId, "visibility", "none");
  }

  function showLayer(layerId: string) {
    map.setLayoutProperty(layerId, "visibility", "visible");
  }

  function getLayerMetadata(layerId: string) {
    return map.getLayer(layerId)?.metadata;
  }

  const setLayerFilters = makeSetLayerFilters({ map, baseUrl });

  const setLayerPopup = makeSetLayerPopup({ map });

  function getZoom() {
    return map.getZoom();
  }

  function getCenter() {
    return map.getCenter().toArray();
  }

  function addEventListener<T extends keyof maplibregl.MapEventType>(
    type: T,
    listener: (ev: maplibregl.MapEventType[T] & Object) => void,
  ): maplibregl.Subscription {
    return map.on(type, listener);
  }

  addStyleDataListener({
    map,
    el,
    setLayerPopup,
  });

  return {
    mapInstance: map,
    hideLayer,
    showLayer,
    setLayerFilters,
    getLayerMetadata,
    setLayerPopup,
    getZoom,
    getCenter,
    addEventListener,
  };
}
