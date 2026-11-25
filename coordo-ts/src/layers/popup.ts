/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

import type {
  GeoJSONSource,
  MapLayerEventType,
  MapLayerMouseEvent,
  MapLayerTouchEvent,
  Map as MapLibreMap,
  PopupOptions,
} from "maplibre-gl";
import { Popup } from "maplibre-gl";

import type { LayerMetadata } from "../types";

/**
 * Handle on an open popup, passed as the last argument of `renderCallback`.
 *
 * Lets the content follow the data of its feature, and clean up after itself
 * however the popup is closed (map click, close button, `close()`).
 */
export type PopupContext<T> = {
  /**
   * Called each time `setLayerFilters` replaces the data of the popup's source,
   * with the new properties of the feature the popup was opened on, or `null`
   * when no feature matches its `featureKey` anymore.
   *
   * Never called when `setLayerPopup` was given no `featureKey`.
   *
   * @returns A function removing the listener.
   */
  onPropertiesChange: (listener: (properties: T | null) => void) => () => void;
  /**
   * Called once when the popup closes, however it is closed: the place to
   * unmount the content (e.g. a React root).
   *
   * @returns A function removing the listener.
   */
  onClose: (listener: () => void) => () => void;
  /** Close the popup, e.g. from a custom close button. */
  close: () => void;
};

export type SetLayerPopupParams<T> = {
  layerId: string;
  trigger: keyof MapLayerEventType;
  renderCallback: (
    properties: T,
    layerMetadata: LayerMetadata,
    context: PopupContext<T>,
  ) => HTMLElement | string;
  popupConfig?: PopupOptions;
  centerOnClick?: boolean;
  /**
   * Properties identifying a feature across data reloads, typically the
   * `groupby` columns of the layer.
   *
   * Feature ids can't be used: they are the row index of the data, so they
   * change as soon as `setLayerFilters` re-aggregates it. With a key, an open
   * popup finds its feature again in the new data and is notified through
   * {@link PopupContext.onPropertiesChange}. Without one, it keeps the
   * properties it was opened with.
   */
  featureKey?: string[];
};

type FeatureProperties = Record<string, unknown>;

/** An open popup that asked to follow the data of its feature. */
type TrackedPopup = {
  featureKey: string[];
  keyValues: unknown[];
  listeners: Set<(properties: FeatureProperties | null) => void>;
};

const getFeatures = (data: GeoJSON.GeoJSON): GeoJSON.Feature[] => {
  if (data.type === "FeatureCollection") {
    return data.features;
  }
  return data.type === "Feature" ? [data] : [];
};

export function makeSetLayerPopup({ map }: { map: MapLibreMap }) {
  /**
   * When setLayerPopup is called for a layer that has already
   * a click listener, we need to remove it before setting the new one
   */
  const popupRemovers: { [layerId: string]: () => void } = {};

  /** Open popups with a `featureKey`, by source id, until they are closed. */
  const trackedPopups = new Map<string, Set<TrackedPopup>>();

  /**
   * Push the new data of a source to its open popups. Called once the data
   * fetched by `setLayerFilters` is on the map.
   */
  function notifyDataReplaced({
    sourceId,
    data,
  }: {
    sourceId: string;
    data: GeoJSON.GeoJSON;
  }) {
    const popups = trackedPopups.get(sourceId);
    if (!popups || popups.size === 0) {
      return;
    }

    const features = getFeatures(data);
    for (const tracked of popups) {
      // Strict equality: both loads come from the same backend columns, so a
      // value keeps its type from one load to the next.
      const match = features.find((feature) =>
        tracked.featureKey.every(
          (property, index) =>
            feature.properties?.[property] === tracked.keyValues[index],
        ),
      );
      const properties = (match?.properties as FeatureProperties) ?? null;
      // Copied: a listener may unsubscribe while we iterate.
      for (const listener of [...tracked.listeners]) {
        listener(properties);
      }
    }
  }

  /**
   * Build the context of a popup and start tracking it when it has a key.
   * Everything is released on the popup `close` event.
   */
  function createPopupContext<T>({
    popup,
    sourceId,
    featureKey,
    properties,
  }: {
    popup: Popup;
    sourceId: string;
    featureKey: string[] | undefined;
    properties: FeatureProperties;
  }): PopupContext<T> {
    const closeListeners = new Set<() => void>();
    const tracked: TrackedPopup | undefined = featureKey
      ? {
          featureKey,
          keyValues: featureKey.map((property) => properties[property]),
          listeners: new Set(),
        }
      : undefined;

    if (tracked) {
      let popups = trackedPopups.get(sourceId);
      if (!popups) {
        popups = new Set();
        trackedPopups.set(sourceId, popups);
      }
      popups.add(tracked);
    }

    popup.once("close", () => {
      if (tracked) {
        trackedPopups.get(sourceId)?.delete(tracked);
        tracked.listeners.clear();
      }
      for (const listener of [...closeListeners]) {
        listener();
      }
      closeListeners.clear();
    });

    return {
      close: () => {
        popup.remove();
      },
      onClose: (listener) => {
        closeListeners.add(listener);
        return () => {
          closeListeners.delete(listener);
        };
      },
      onPropertiesChange: (listener) => {
        const untyped = listener as (
          properties: FeatureProperties | null,
        ) => void;
        tracked?.listeners.add(untyped);
        return () => {
          tracked?.listeners.delete(untyped);
        };
      },
    };
  }

  /**
   * Sets up a popup for a specific map layer, triggered by user interaction.
   * The popup content is generated by a callback function, which can return either
   * a string (HTML) or a DOM element.
   *
   * @template T - The type of the GeoJSON properties for the layer's features.
   * @param {Object} params - Parameters for setting up the popup.
   * @param {string} params.layerId - Name of the layer to attach the popup to.
   * @param {keyof MapLayerEventType} params.trigger - Type of event that triggers the popup (e.g., "click", "mouseenter").
   * @param {(properties: T) => HTMLElement | string} params.renderCallback - Callback that generates the popup content.
   *   Accepts the feature's properties and returns either a DOM element or a string of HTML.
   * @param {PopupOptions} [params.popupConfig] - Configuration for the popup (e.g., offset, anchor, className).
   * @param {boolean} params.centerOnClick - Whether to center the map after clicking on a popup symbol
   * @param {string[]} [params.featureKey] - Properties identifying a feature across data reloads. With it,
   *   the popup is notified (see {@link PopupContext.onPropertiesChange}) when `setLayerFilters` replaces the data.
   *
   * @example
   * // Example with HTML string
   * const renderPopup = (properties) => {
   *   return `<div class="popup-content">
   *     <h3>${properties.name}</h3>
   *     <p>Value: ${properties.value}</p>
   *   </div>`;
   * };
   *
   * mapApiRef.current.setLayerPopup({
   *   layerId: "my-layer-id",
   *   trigger: "click",
   *   renderCallback: renderPopup,
   *   popupConfig: {
   *     className: "custom-popup",
   *     closeButton: true,
   *     anchor: "bottom",
   *   },
   *   centerOnClick: true,
   * });
   *
   * @example
   * // Example with DOM element
   * const renderPopup = (properties) => {
   *   const div = document.createElement("div");
   *   div.innerHTML = `<h3>${properties.name}</h3><p>Value: ${properties.value}</p>`;
   *   return div;
   * };
   *
   * mapApiRef.current.setLayerPopup({
   *   layerId: "my-layer-id",
   *   trigger: "click",
   *   renderCallback: renderPopup,
   *   centerOnClick: true
   * });
   *
   * @example
   * // Example following the data: the popup is refreshed when setLayerFilters
   * // recomputes the layer, and unmounted however it is closed
   * const renderPopup = (properties, metadata, context) => {
   *   const div = document.createElement("div");
   *   const render = (props) => {
   *     div.textContent = props ? `${props.household_nb} households` : "No match";
   *   };
   *   render(properties);
   *   context.onPropertiesChange(render);
   *   return div;
   * };
   *
   * mapApiRef.current.setLayerPopup({
   *   featureKey: ["proj", "loc1", "loc2", "year"],
   *   layerId: "enquete",
   *   trigger: "click",
   *   renderCallback: renderPopup,
   * });
   */
  function setLayerPopup<T extends Record<string, unknown>>({
    layerId,
    trigger,
    renderCallback,
    popupConfig,
    centerOnClick,
    featureKey,
  }: SetLayerPopupParams<T>) {
    if (layerId in popupRemovers) {
      popupRemovers[layerId]?.(); // Cleanup precedent trigger
      delete popupRemovers[layerId];
    }

    const onTrigger = async (ev: MapLayerMouseEvent | MapLayerTouchEvent) => {
      const lngLat = ev.lngLat;
      const eventProps = ev.features?.[0]?.properties;
      const id = ev.features?.[0]?.id;
      if (lngLat && Number(id) >= 0 && eventProps) {
        /** @todo Remove "any" casting  */
        const popup = new Popup(popupConfig).setLngLat(ev.lngLat);

        const layer = map.getLayer(layerId);
        const sourceId = layer?.source ?? layerId;
        const source = map.getSource(sourceId) as GeoJSONSource;
        const data = await source.getData();
        const properties = Object.assign(eventProps, {
          /**
           * MapLibre Events will remove any non-string and non-numeric properties from object definition
           * see https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#querysourcefeatures
           * We want to add them back because we use complex object and potential null values
           */
          // @ts-expect-error - MapLibre types are not accurate regarding feature properties
          ...data.features?.find((f) => Number(f.id) === Number(id))
            ?.properties,
        }) as T;

        const layerMetadata = layer?.metadata as LayerMetadata;
        const context = createPopupContext<T>({
          featureKey,
          popup,
          properties,
          sourceId,
        });
        const content = renderCallback(properties as T, layerMetadata, context);
        if (typeof content === "string") {
          popup.setHTML(content);
        } else {
          popup.setDOMContent(content);
        }
        popup.addTo(map);
      } else if (!lngLat) {
        console.warn("Missing property lngLat on event : ", ev);
      } else if (!ev.features) {
        console.warn("Event features not found");
      } else if (!(Number(id) >= 0)) {
        console.warn("event feature id is invalid: ", id);
      } else if (!eventProps) {
        console.warn("Event feature properties not found", eventProps);
      }
    };

    // Add "trigger" listener
    map.on(trigger, layerId, onTrigger);

    //  Add Mouse listeners
    const onMouseEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const onMouseLeave = () => {
      map.getCanvas().style.cursor = "";
    };

    if (centerOnClick) {
      /**
       * @link https://maplibre.org/maplibre-gl-js/docs/examples/center-the-map-on-a-clicked-symbol/
       */
      map.on("click", layerId, (e) => {
        const geometry = e?.features?.[0]?.geometry;
        if (geometry && "coordinates" in geometry) {
          let posX: number | undefined;
          let posY: number | undefined;

          if (geometry.type === "Point") {
            /** Points coordinates: [-90.3295,-0.6344474832838974]
             * => fly to this position */
            const [coordo1, coordo2] = geometry.coordinates;
            posX = coordo1;
            posY = coordo2;
          }

          if (geometry.type === "Polygon") {
            /** Polygon coordinates: [[[XXX,YYY], [XXX,YYY], [XXX,YYY], ...]]
             * => fly to the centroid, e.g. [mean of XXXs, mean of YYYs] */
            const polygonPoints = geometry.coordinates.flat();
            const nbOfPoints = polygonPoints.length;
            const { sumX, sumY } = polygonPoints.reduce<{
              sumX: number;
              sumY: number;
            }>(
              (acc, point) => {
                const [pointX, pointY] = point;
                return {
                  sumX: acc.sumX + (pointX ?? 0),
                  sumY: acc.sumY + (pointY ?? 0),
                };
              },
              { sumX: 0, sumY: 0 },
            );

            posX = sumX / nbOfPoints;
            posY = sumY / nbOfPoints;
          }

          if (posX != null && posY != null) {
            map.flyTo({
              center: [posX, posY],
            });
          }
        }
      });
    }

    if (trigger.includes("click")) {
      map.on("mouseenter", layerId, onMouseEnter);
      map.on("mouseleave", layerId, onMouseLeave);
    }

    // Define cleanup function
    const removeListeners = () => {
      map.off(trigger, layerId, onTrigger);
      if (trigger.includes("click")) {
        map.off("mouseenter", layerId, onMouseEnter);
        map.off("mouseleave", layerId, onMouseLeave);
      }
    };

    // Add cleanup function to regitry
    popupRemovers[layerId] = removeListeners;
  }

  return { notifyDataReplaced, setLayerPopup };
}
