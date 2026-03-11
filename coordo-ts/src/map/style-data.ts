import type {
  Map as MapLibreMap,
  MapLayerEventType,
  StyleSpecification,
  ControlPosition,
  LayerSpecification,
} from "maplibre-gl";
import { NavigationControl, ScaleControl } from "maplibre-gl";

import { CONTROLS, LayerControl } from "../layers/controls";
import type { LayerMetadata } from "../types";
import type { SetLayerPopupParams } from "../layers/popup";

export type StyleMetaData = {
  controls: Array<{
    type: string;
    position: ControlPosition;
  }>;
};

function renderTemplate(html: string, vars: Record<string, string>) {
  return html.replace(/{{\s*(\w+)\s*}}/g, (_, key) => vars[key] ?? "");
}

export function addStyleDataListener({
  map,
  el,
  setLayerPopup,
}: {
  map: MapLibreMap;
  el: HTMLElement;
  setLayerPopup: (params: SetLayerPopupParams<Record<string, string>>) => void;
}) {
  let style: StyleSpecification | undefined;
  let controlsAdded = false;

  function init() {
    el.dispatchEvent(new CustomEvent("map:ready"));
  }

  map.on("styledata", () => {
    if (controlsAdded) {
      console.warn("[STYLEDATA] Controls already setup.");
      return;
    }
    controlsAdded = true;

    style = map.getStyle();

    /**
     * Configure Controls based on metadata
     */
    const controls = (style.metadata as StyleMetaData).controls || [];
    controls.forEach((config) => {
      switch (config.type) {
        case CONTROLS.COMPASS:
          map.addControl(
            new NavigationControl({ showZoom: false }),
            config.position,
          );
          break;

        case CONTROLS.ZOOM:
          map.addControl(
            new NavigationControl({ showCompass: false }),
            config.position,
          );
          break;

        case CONTROLS.LAYER:
          map.addControl(new LayerControl(), config.position);
          break;

        case CONTROLS.SCALE:
          map.addControl(new ScaleControl(), config.position);
          break;
      }
    });

    // Configure layers based on metadata
    const layers = style.layers || [];
    layers.forEach((layer: LayerSpecification) => {
      const metadata = layer.metadata as LayerMetadata;

      // Default HTML generation for Popup metadata
      const isPopupMetadata = metadata?.popup !== undefined;
      if (isPopupMetadata) {
        setLayerPopup({
          layerId: layer.id,
          renderCallback: (props) => {
            if (metadata.popup?.html) {
              // When the backend data contains html, render it
              return renderTemplate(
                metadata.popup?.html ?? "<h1>Undefined</h1>",
                props,
              );
            }
            return JSON.stringify(props, null, 2);
          },
          trigger: metadata.popup?.trigger as keyof MapLayerEventType,
        });
      }
    });

    init();
  });

  return {
    style,
    controlsAdded,
    init,
  };
}
