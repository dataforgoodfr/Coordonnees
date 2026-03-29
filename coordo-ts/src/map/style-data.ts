import type {
  ControlPosition,
  LayerSpecification,
  MapLayerEventType,
  Map as MapLibreMap,
  StyleSpecification,
} from "maplibre-gl";
import { LngLatBounds, NavigationControl, ScaleControl } from "maplibre-gl";

import { CONTROLS, LayerControl } from "../layers/controls";
import type { SetLayerPopupParams } from "../layers/popup";
import type { LayerMetadata } from "../types";

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
  dispatchEventToConsumer,
  map,
  setLayerPopup,
  onSuccess,
}: {
  dispatchEventToConsumer: (event: CustomEvent) => void;
  map: MapLibreMap;
  setLayerPopup: (params: SetLayerPopupParams<Record<string, string>>) => void;
  onSuccess?: () => void;
}) {
  let style: StyleSpecification | undefined;
  let controlsAdded = false;

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
          map.addControl(new LayerControl({ dispatchEventToConsumer }), config.position);
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
              // If the backend provide html, render it
              return renderTemplate(metadata.popup?.html, props);
            }
            return `<div style="background-color: white">${JSON.stringify(props, null, 2)}</div>`;
          },
          trigger: metadata.popup?.trigger as keyof MapLayerEventType,
        });
      }
    });

    const totalBounds = new LngLatBounds();
    Object.values(style.sources).forEach((source) => {
      if (source.type === "geojson") {
        if (typeof source.data !== "string" && source.data.bbox) {
          const bbox = source.data.bbox.slice(0, 4);
          totalBounds.extend(bbox as [number, number, number, number]);
        }
      }
    });
    map.fitBounds(totalBounds, { padding: 50 });

    onSuccess?.();
  });

  return {
    controlsAdded,
    style,
  };
}
