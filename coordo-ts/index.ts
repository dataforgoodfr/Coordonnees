import maplibregl, {
  ControlPosition,
  GeoJSONSource,
  LayerSpecification,
  Map,
  MapLayerEventType,
  MapLayerMouseEvent,
  MapLayerTouchEvent,
  StyleSpecification,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "./index.css";

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
type MapOptions = {
  zoom: number;
  /**
   * [longitude, latitude]
   */
  center: [number, number];
};
const DEFAULT_MAP_OPTIONS: MapOptions = {
  zoom: 1,
  center: [0, 0],
};

class LayerControl {
  private _map?: Map;
  private _container?: HTMLElement;
  private _panel?: HTMLElement;
  constructor() {}

  onAdd(map: Map) {
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
  options?: Partial<MapOptions>,
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
      if (metadata?.popup != undefined) {
        setLayerPopup(
          layer.id,
          metadata.popup.trigger as keyof MapLayerEventType,
          (props: Record<string, string>) =>
            metadata.popup!.html
              ? renderTemplate(metadata.popup!.html!, props)
              : JSON.stringify(props, null, 2),
        );
      }
    });

    init();
  });

  function init() {
    el.dispatchEvent(new CustomEvent("map:ready"));
  }

  async function setLayerFilters(layerId: string, filters: any) {
    const layer = map.getLayer(layerId);
    if (layer == undefined) {
      throw new Error(`Layer ${layerId} doesn't exist.`);
    }
    let dataUrl = (layer.metadata as LayerMetadata).url;
    if (!dataUrl) {
      throw new Error(`Layer ${layer.id} can't be filtered.`);
    }
    if (!dataUrl.startsWith("http")) {
      dataUrl = new URL(dataUrl, baseUrl).toString();
    }
    const source = map.getSource(layer?.source)!;
    const res = await fetch(dataUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(filters),
    });
    const data = await res.json();
    (source as GeoJSONSource).setData(data);
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

  const popupRemovers: { [key: string]: () => void } = {};
  function setLayerPopup(
    layerId: string,
    trigger: keyof MapLayerEventType,
    callback: (properties: Record<string, string>) => HTMLElement | string,
  ) {
    if (layerId in popupRemovers) {
      popupRemovers[layerId]?.();
      delete popupRemovers[layerId];
    }
    const onTrigger = (
      ev: (MapLayerMouseEvent | MapLayerTouchEvent) & Object,
    ) => {
      const geometry = ev.features?.[0]?.geometry;
      const properties = ev.features?.[0]?.properties;
      if (geometry && properties) {
        // TODO removethis "any"
        const coordinates = (geometry as any).coordinates.slice();
        const popup = new maplibregl.Popup().setLngLat(coordinates);
        const content = callback(properties);
        if (typeof content == "string") {
          popup.setHTML(content);
        } else {
          popup.setDOMContent(content);
        }
        popup.addTo(map);
      }
    };
    const onMouseEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const onMouseLeave = () => {
      map.getCanvas().style.cursor = "";
    };

    map.on(trigger, layerId, onTrigger);
    if (trigger.includes("click")) {
      map.on("mouseenter", layerId, onMouseEnter);
      map.on("mouseleave", layerId, onMouseLeave);
    }
    const removeListeners = () => {
      map.off(trigger, layerId, onTrigger);
      if (trigger.includes("click")) {
        map.off("mouseenter", layerId, onMouseEnter);
        map.off("mouseleave", layerId, onMouseLeave);
      }
    };
    popupRemovers[layerId] = removeListeners;
  }

  function getZoom() {
    return map.getZoom();
  }

  function getCenter() {
    return map.getCenter().toArray();
  }

  function addEventListener<T extends keyof maplibregl.MapEventType>(type: T, listener: (ev: maplibregl.MapEventType[T] & Object) => void): maplibregl.Subscription {
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
