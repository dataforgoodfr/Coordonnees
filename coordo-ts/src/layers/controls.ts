import type { LayerSpecification, Map as MapLibreMap } from "maplibre-gl";

import { EVENTS } from "../events";

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
  private _dispatchEvent: (eventName: string) => void;
  private _syncFunctions: Record<string, () => void>;

  constructor({
    dispatchEventToConsumer,
  }: { dispatchEventToConsumer: (event: CustomEvent) => void }) {
    this._dispatchEvent = (eventName: string) =>
      dispatchEventToConsumer(new CustomEvent(eventName));
    this._syncFunctions = {};
  }

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

  _isChecked(layerId: string) {
    return (
      this._map?.getLayoutProperty(layerId, "visibility") !==
      LAYER_VISIBILITY.NONE
    );
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
      checkbox.checked = this._isChecked(layerId);

      checkbox.addEventListener("change", () => {
        const isChecked = checkbox.checked;
        this._map?.setLayoutProperty(
          layerId,
          "visibility",
          isChecked ? LAYER_VISIBILITY.VISIBLE : LAYER_VISIBILITY.NONE,
        );
        this._dispatchEvent(
          isChecked ? EVENTS.LAYER_SHOW(layerId) : EVENTS.LAYER_HIDE(layerId),
        );
      });

      const syncCheckboxState = () => {
        checkbox.checked = this._isChecked(layerId);
      };

      this._syncFunctions[layerId] = syncCheckboxState;

      label.appendChild(checkbox);
      label.appendChild(document.createTextNode(` ${layerId}`));

      this._panel?.appendChild(label);
    });
  }

  onRemove() {
    this._container?.remove();
    this._map = undefined;
  }

  syncState() {
    const layers = this._map?.getStyle().layers;

    layers?.forEach((layer: LayerSpecification) => {
      const layerId = layer.id;
      this._syncFunctions[layerId]?.();
    });
  }
}
