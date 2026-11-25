/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

import type { Map as MapLibreMap } from "maplibre-gl";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { makeSetLayerPopup, type PopupContext } from "./popup";

const { POPUPS } = vi.hoisted(() => ({ POPUPS: [] as FakePopup[] }));

type FakePopup = {
  isOpen: boolean;
  content: unknown;
  remove: () => FakePopup;
};

vi.mock("maplibre-gl", () => {
  class Popup implements FakePopup {
    isOpen = false;
    content: unknown;
    private closeListeners: Array<() => void> = [];

    constructor() {
      POPUPS.push(this);
    }
    setLngLat() {
      return this;
    }
    setHTML(html: string) {
      this.content = html;
      return this;
    }
    setDOMContent(element: unknown) {
      this.content = element;
      return this;
    }
    addTo() {
      this.isOpen = true;
      return this;
    }
    once(type: string, listener: () => void) {
      if (type === "close") {
        this.closeListeners.push(listener);
      }
      return this;
    }
    remove() {
      if (this.isOpen) {
        this.isOpen = false;
        const listeners = this.closeListeners;
        this.closeListeners = [];
        for (const listener of listeners) {
          listener();
        }
      }
      return this;
    }
  }
  return { Popup };
});

type Properties = {
  proj: string;
  loc2: number;
  household_nb: number;
};

const feature = (id: number, properties: Properties) => ({
  geometry: { coordinates: [0, 0], type: "Point" },
  id,
  properties,
  type: "Feature",
});

const collection = (...features: ReturnType<typeof feature>[]) =>
  ({ features, type: "FeatureCollection" }) as GeoJSON.FeatureCollection;

const VILLAGE_A = { household_nb: 10, loc2: 1, proj: "A" };
const VILLAGE_B = { household_nb: 4, loc2: 2, proj: "A" };

function setup() {
  const handlers = new Map<string, (event: unknown) => Promise<void>>();
  const map = {
    getCanvas: () => ({ style: {} }),
    getLayer: (layerId: string) =>
      layerId === "enquete"
        ? { metadata: { popup: undefined }, source: "enquete-source" }
        : undefined,
    getSource: (sourceId: string) =>
      sourceId === "enquete-source"
        ? {
            getData: async () =>
              collection(feature(0, VILLAGE_A), feature(1, VILLAGE_B)),
          }
        : undefined,
    off: vi.fn(),
    on: (type: string, layerId: string, handler: () => Promise<void>) => {
      handlers.set(`${type}:${layerId}`, handler);
    },
  } as unknown as MapLibreMap;

  const { notifyDataReplaced, setLayerPopup } = makeSetLayerPopup({ map });

  let context: PopupContext<Properties> | undefined;
  const renderCallback = vi.fn(
    (
      _properties: Properties,
      _metadata: unknown,
      ctx: PopupContext<Properties>,
    ) => {
      context = ctx;
      return "<p>popup</p>";
    },
  );

  /** Open the popup on village A, the second feature of the source. */
  const openPopup = async (featureKey?: string[]) => {
    setLayerPopup<Properties>({
      featureKey,
      layerId: "enquete",
      renderCallback,
      trigger: "click",
    });
    await handlers.get("click:enquete")?.({
      features: [{ id: 0, properties: { ...VILLAGE_A } }],
      lngLat: { lat: 0, lng: 0 },
    });
    if (!context) {
      throw new Error("The popup was not rendered");
    }
    return context;
  };

  return { notifyDataReplaced, openPopup, renderCallback };
}

beforeEach(() => {
  POPUPS.length = 0;
});

describe("setLayerPopup", () => {
  it("renders the clicked feature's properties with a context", async () => {
    const { openPopup, renderCallback } = setup();

    await openPopup();

    expect(renderCallback).toHaveBeenCalledExactlyOnceWith(
      VILLAGE_A,
      { popup: undefined },
      expect.objectContaining({
        close: expect.any(Function),
        onClose: expect.any(Function),
        onPropertiesChange: expect.any(Function),
      }),
    );
    expect(POPUPS[0]?.content).toBe("<p>popup</p>");
  });

  it("sends the feature's new properties, matched on the key, not the id", async () => {
    const { notifyDataReplaced, openPopup } = setup();
    const context = await openPopup(["proj", "loc2"]);
    const listener = vi.fn();
    context.onPropertiesChange(listener);

    const recomputed = { ...VILLAGE_A, household_nb: 3 };
    notifyDataReplaced({
      // Re-aggregated: the features are renumbered.
      data: collection(feature(0, VILLAGE_B), feature(1, recomputed)),
      sourceId: "enquete-source",
    });

    expect(listener).toHaveBeenCalledExactlyOnceWith(recomputed);
  });

  it("sends null when no feature matches the key anymore", async () => {
    const { notifyDataReplaced, openPopup } = setup();
    const context = await openPopup(["proj", "loc2"]);
    const listener = vi.fn();
    context.onPropertiesChange(listener);

    notifyDataReplaced({
      data: collection(feature(0, VILLAGE_B)),
      sourceId: "enquete-source",
    });

    expect(listener).toHaveBeenCalledExactlyOnceWith(null);
  });

  it("compares key values strictly", async () => {
    const { notifyDataReplaced, openPopup } = setup();
    const context = await openPopup(["proj", "loc2"]);
    const listener = vi.fn();
    context.onPropertiesChange(listener);

    notifyDataReplaced({
      data: collection(
        feature(0, { ...VILLAGE_A, loc2: "1" as unknown as number }),
      ),
      sourceId: "enquete-source",
    });

    expect(listener).toHaveBeenCalledExactlyOnceWith(null);
  });

  it("ignores the data of other sources", async () => {
    const { notifyDataReplaced, openPopup } = setup();
    const context = await openPopup(["proj", "loc2"]);
    const listener = vi.fn();
    context.onPropertiesChange(listener);

    notifyDataReplaced({
      data: collection(feature(0, VILLAGE_A)),
      sourceId: "other-source",
    });

    expect(listener).not.toHaveBeenCalled();
  });

  it("never notifies a popup opened without a feature key", async () => {
    const { notifyDataReplaced, openPopup } = setup();
    const context = await openPopup();
    const listener = vi.fn();
    context.onPropertiesChange(listener);

    notifyDataReplaced({
      data: collection(feature(0, VILLAGE_A)),
      sourceId: "enquete-source",
    });

    expect(listener).not.toHaveBeenCalled();
  });

  it("stops notifying a listener once it unsubscribed", async () => {
    const { notifyDataReplaced, openPopup } = setup();
    const context = await openPopup(["proj", "loc2"]);
    const listener = vi.fn();
    const unsubscribe = context.onPropertiesChange(listener);

    unsubscribe();
    notifyDataReplaced({
      data: collection(feature(0, VILLAGE_A)),
      sourceId: "enquete-source",
    });

    expect(listener).not.toHaveBeenCalled();
  });

  it("calls the close listeners once and stops tracking a closed popup", async () => {
    const { notifyDataReplaced, openPopup } = setup();
    const context = await openPopup(["proj", "loc2"]);
    const onClose = vi.fn();
    const listener = vi.fn();
    context.onClose(onClose);
    context.onPropertiesChange(listener);

    context.close();
    // Closing again (e.g. a map click after the close button) is a no-op.
    POPUPS[0]?.remove();
    notifyDataReplaced({
      data: collection(feature(0, VILLAGE_A)),
      sourceId: "enquete-source",
    });

    expect(POPUPS[0]?.isOpen).toBe(false);
    expect(onClose).toHaveBeenCalledOnce();
    expect(listener).not.toHaveBeenCalled();
  });

  it("does not call a close listener that unsubscribed", async () => {
    const { openPopup } = setup();
    const context = await openPopup();
    const onClose = vi.fn();
    const unsubscribe = context.onClose(onClose);

    unsubscribe();
    context.close();

    expect(onClose).not.toHaveBeenCalled();
  });
});
