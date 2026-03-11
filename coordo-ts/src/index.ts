import maplibregl, {
  type ControlPosition,
  type GeoJSONSource,
  type LayerSpecification,
  type Map as MapLibreMap,
  type MapLayerEventType,
  type StyleSpecification,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "./index.css";
import type { LayerMetadata } from "./types";
import { makeSetLayerPopup } from "./layers/popup";
import { makeSetLayerFilters } from "./layers/filters";

type StyleMetaData = {
  controls: Array<{
    type: string;
    position: ControlPosition;
  }>;
};

const DEFAULT_MAP_OPTIONS: Partial<maplibregl.MapOptions> = {
  zoom: 1,
  center: [0, 0],
};

class LayerControl {
  private _map?: MapLibreMap;
  private _container?: HTMLElement;
  private _panel?: HTMLElement;

  onAdd(map: MapLibreMap) {
    this._map = map;
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    this._container.innerHTML = "<button>L</button>";

    this._panel = document.createElement("div");
    this._panel.className =
      "maplibregl-ctrl-group maplibregl-ctrl-layer hidden";
    this._buildLayerList();
    this._container.appendChild(this._panel);

    this._container.addEventListener("click", () =>
      this._panel?.classList.toggle("hidden"),
    );

    this._panel.addEventListener("click", (e) => e.stopPropagation());
    this._map?.on("click", () => this._panel?.classList.add("hidden"));

    return this._container;
  }

  _buildLayerList() {
    const layers = this._map?.getStyle().layers;

    layers?.forEach((layer: LayerSpecification) => {
      const layerId = layer.id;

      const label = document.createElement("label");
      label.style.display = "flex";
      label.style.cursor = "pointer";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked =
        this._map?.getLayoutProperty(layerId, "visibility") !== "none";

      checkbox.addEventListener("change", () => {
        this._map?.setLayoutProperty(
          layerId,
          "visibility",
          checkbox.checked ? "visible" : "none",
        );
      });

      label.appendChild(checkbox);
      label.appendChild(document.createTextNode(" " + layerId));

      this._panel?.appendChild(label);
    });
  }

  onRemove() {
    this._container?.remove();
    this._map = undefined;
  }
}

function renderTemplate(html: string, vars: Record<string, string>) {
  return html.replace(/{{\s*(\w+)\s*}}/g, (_, key) => vars[key] ?? "");
}

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
  let style: StyleSpecification;

  let controlsAdded = false;
  map.on("styledata", () => {
    if (controlsAdded) return;
    controlsAdded = true;
    style = map.getStyle();
    const controls = (style.metadata as StyleMetaData).controls || [];

    controls.forEach((config) => {
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
