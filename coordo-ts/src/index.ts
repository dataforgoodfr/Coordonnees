import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import "./index.css";

<<<<<<< feat/external-data
type StyleMetaData = {
  controls: Array<{
    type: string;
    position: ControlPosition;
  }>;
};

type LayerMetadata = {
  popup?: {
    trigger: string;
    html?: string;
  };
  url?: string;
};
=======
import { LAYER_VISIBILITY } from "./layers/controls";
import { makeSetLayerFilters } from "./layers/filters";
import { makeSetLayerPopup } from "./layers/popup";
import { addStyleDataListener } from "./map/style-data";
>>>>>>> main

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

<<<<<<< feat/external-data
  if (!el) throw new Error("Map target not found");
  const baseUrl = new URL("./", new URL(styleUrl, window.location.href)).href;
=======
  if (!el) {
    throw new Error("[CREATE] Map target not found");
  }

  const baseUrl = styleUrl.startsWith("http")
    ? new URL(styleUrl).origin
    : window.location.href;
>>>>>>> main

  const mergedOptions = { ...DEFAULT_MAP_OPTIONS, ...options };

  const map = new maplibregl.Map({
    center: mergedOptions.center,
    container: el,
    style: styleUrl,
    zoom: mergedOptions.zoom,
  });
<<<<<<< feat/external-data

  let style: StyleSpecification;
  let controlsAdded: string[] = [];
  map.on("styledata", () => {
    style = map.getStyle();
    const controls = (style.metadata as StyleMetaData).controls || [];
    controls.forEach((config) => {
      if (controlsAdded.includes(config.type)) {
        return;
      }
      controlsAdded.push(config.type);
      switch (config.type) {
        case "compass":
          map.addControl(
            new maplibregl.NavigationControl({ showZoom: false }),
            config.position,
          );
          break;
        case "zoom":
          map.addControl(
            new maplibregl.NavigationControl({ showCompass: false }),
            config.position,
          );
          break;
        case "layer":
          map.addControl(new LayerControl(), config.position);
          break;
        case "scale":
          map.addControl(new maplibregl.ScaleControl(), config.position);
          break;
      }
    });

    const layers = style.layers || [];

    layers.forEach((layer: LayerSpecification) => {
      const metadata = layer.metadata as LayerMetadata;
      if (metadata?.popup !== undefined) {
        setLayerPopup({
          layerId: layer.id,
          renderCallback: (props: Record<string, string>) =>
            metadata.popup?.html
              ? renderTemplate(
                  metadata.popup?.html ?? "<h1>Undefined</h1>",
                  props,
                )
              : JSON.stringify(props, null, 2),
          trigger: metadata.popup.trigger as keyof MapLayerEventType,
        });
      }
    });

    init();
  });

  function init() {
    el.dispatchEvent(new CustomEvent("map:ready"));
  }

  async function setLayerFilters(layerId: string, filters: any) {
    const layer = map.getLayer(layerId);
    if (layer === undefined) {
      throw new Error(`Layer ${layerId} doesn't exist.`);
    }
    const dataUrl = new URL(layerId, baseUrl).toString();
    const source = map.getSource(layer?.source)!;
    const res = await fetch(dataUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(filters),
    });
    const data = await res.json();
    (source as GeoJSONSource).setData(data);
  }
=======
>>>>>>> main

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
