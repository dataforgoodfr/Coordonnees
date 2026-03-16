import type { LayerSpecification, Map as MapLibreMap } from "maplibre-gl";

export const CONTROLS = {
  COMPASS: "compass",
  LAYER: "layer",
  SCALE: "scale",
  ZOOM: "zoom",
} as const;

export type ControlKind = (typeof CONTROLS)[keyof typeof CONTROLS];

export const LAYER_VISIBILITY = {
  NONE: "none",
  VISIBLE: "visible",
} as const;

export class LayerControl {
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

    // For each layer, create an inline selector made of a label and a checkbox
    layers?.forEach((layer: LayerSpecification) => {
      const layerId = layer.id;

      const label = document.createElement("label");
      label.style.display = "flex";
      label.style.cursor = "pointer";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked =
        this._map?.getLayoutProperty(layerId, "visibility") !==
        LAYER_VISIBILITY.NONE;

      checkbox.addEventListener("change", () => {
        this._map?.setLayoutProperty(
          layerId,
          "visibility",
          checkbox.checked ? LAYER_VISIBILITY.VISIBLE : LAYER_VISIBILITY.NONE,
        );
      });

      label.appendChild(checkbox);
      label.appendChild(document.createTextNode(` ${layerId}`));

      this._panel?.appendChild(label);
    });
  }

  onRemove() {
    this._container?.remove();
    this._map = undefined;
  }
}
