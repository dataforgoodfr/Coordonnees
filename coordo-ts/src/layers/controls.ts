/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

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

export const LAYER_CONTROL_ELEMENTS = {
  ANCHOR: "layer-control-anchor",
  LAYER_ROW: (layerId: string) => `layer-control-row-${layerId}`,
  PANEL: "layer-control-panel",
} as const;

export type LayerControlRenderAnchor =
  | (() => string | HTMLElement)
  | null
  | undefined;
export type LayerControlRenderLayerRow =
  | ((params: {
      layerId: string;
      isChecked: boolean;
      onClick: (nextChecked?: boolean) => void;
      container?: HTMLElement; // Pass the container for pure JS/HTML
    }) => string | HTMLElement | null | undefined)
  | null
  | undefined;

export type LayerControlConstructorProps = {
  dispatchEventToConsumer: (event: CustomEvent) => void;
  renderAnchor?: LayerControlRenderAnchor;
  renderLayerRow?: LayerControlRenderLayerRow;
};

export class LayerControl {
  private _map?: MapLibreMap;
  private _container?: HTMLElement;
  private _panel?: HTMLElement;
  private _dispatchEvent: (eventName: string) => void;
  private _syncFunctions: Record<string, () => void>;
  private _renderAnchor?: LayerControlRenderAnchor;
  private _renderLayerRow?: LayerControlRenderLayerRow;

  constructor({
    dispatchEventToConsumer,
    renderAnchor,
    renderLayerRow,
  }: LayerControlConstructorProps) {
    this._dispatchEvent = (eventName: string) =>
      dispatchEventToConsumer(new CustomEvent(eventName));
    this._syncFunctions = {};
    this._renderAnchor = renderAnchor;
    this._renderLayerRow = renderLayerRow;
  }

  onAdd(map: MapLibreMap) {
    this._map = map;

    this._container = document.createElement("div");
    this._container.id = LAYER_CONTROL_ELEMENTS.ANCHOR;
    this._container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    const content = this._renderAnchor?.() ?? "<button>L</button>";
    if (typeof content === "string") {
      this._container.innerHTML = content;
    } else {
      this._container.appendChild(content);
    }

    this._panel = document.createElement("div");
    this._panel.id = LAYER_CONTROL_ELEMENTS.PANEL;
    this._panel.className =
      "maplibregl-ctrl-group maplibregl-ctrl-layer hidden";
    this._panel.addEventListener("click", (e) => e.stopPropagation());
    this._buildLayerList();

    this._container.appendChild(this._panel);
    this._container.addEventListener("click", () =>
      this._panel?.classList.toggle("hidden"),
    );

    // Similar to a "clickOutsideListener"
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
      label.id = LAYER_CONTROL_ELEMENTS.LAYER_ROW(layerId);
      label.classList.add("coordo__w-full");

      // Dispatch state update to map layout property
      const onClick = (isChecked: boolean) => {
        this._map?.setLayoutProperty(
          layerId,
          "visibility",
          isChecked ? LAYER_VISIBILITY.VISIBLE : LAYER_VISIBILITY.NONE,
        );
        this._dispatchEvent(
          isChecked ? EVENTS.LAYER_SHOW(layerId) : EVENTS.LAYER_HIDE(layerId),
        );
      };

      if (this._renderLayerRow) {
        this._renderCustomLayerRow({
          layerId,
          onClick,
          rowContainer: label,
        });
      } else {
        this._renderVanillaLayerRow({
          layerId,
          onClick,
          rowContainer: label,
        });
      }

      this._panel?.appendChild(label);
    });
  }

  _renderCustomLayerRow({
    rowContainer,
    layerId,
    onClick,
  }: {
    rowContainer: HTMLElement;
    onClick: (isChecked: boolean) => void;
    layerId: string;
  }) {
    /**
     * Define the props to provide to renderLayerRow, using the latest
     * layer state from the Map state.
     */
    const getCurrentContentConfig = () => ({
      isChecked: this._isChecked(layerId),
      layerId,
      onClick: (nextChecked?: boolean) => {
        const nextState = nextChecked ?? !this._isChecked(layerId);
        onClick(nextState);
      },
      rowContainer, // Pass the container to the render function
    });

    /**
     * Get the updated content with the latest configuration
     * and replace either the html content or the previous node
     * with a new one (remount)
     */
    const mountLayerRow = () => {
      if (!this._renderLayerRow) {
        return;
      }

      const currentConfig = getCurrentContentConfig();
      const newContent = this._renderLayerRow(currentConfig);

      if (!newContent) {
        return;
      }

      if (typeof newContent === "string") {
        rowContainer.innerHTML = newContent;
        return;
      }

      // If a child already exist, it has a staled state
      // => we replace it with a new child containing the newest state
      if (rowContainer.firstChild) {
        rowContainer.replaceChild(newContent, rowContainer.firstChild);
      } else {
        // Else we just inject the new child (first render)
        rowContainer.appendChild(newContent);
      }
    };

    // Initial render
    mountLayerRow();

    // Sync function: Remount the Layer Row inside the container
    this._syncFunctions[layerId] = mountLayerRow;
  }

  _renderVanillaLayerRow({
    rowContainer,
    layerId,
    onClick,
  }: {
    rowContainer: HTMLElement;
    onClick: (isChecked: boolean) => void;
    layerId: string;
  }) {
    // Create a "local" checkbox for which we need to sync the "checked" state with the global state
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";

    checkbox.checked = this._isChecked(layerId);

    // When checkbox is clicked: Checkbox state --> Map Layout State
    checkbox.addEventListener("change", () => {
      onClick(checkbox.checked);
    });

    // When Map Layout State change: Map Layout State --> Checkbox state
    const syncCheckboxState = () => {
      checkbox.checked = this._isChecked(layerId);
    };
    this._syncFunctions[layerId] = syncCheckboxState;

    const text = document.createElement("span");
    text.textContent = layerId;
    text.className = "coordo__ml-xs";

    rowContainer.appendChild(checkbox);
    rowContainer.appendChild(text);
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
