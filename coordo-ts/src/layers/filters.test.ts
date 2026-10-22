/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

import type { Map as MapLibreMap } from "maplibre-gl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { cql } from "./cql";
import { makeLayerFilters } from "./filters";
import { setSourceData } from "./source-filter";

vi.mock("./source-filter", () => ({ setSourceData: vi.fn() }));

const BASE_URL = new URL("https://api.example.org/maps/");

const LAYERS: Record<string, object> = {
  // Not a datapackage layer: no resource schema to validate against
  basemap: { source: "basemap-source" },
  enquete: {
    metadata: {
      resource: {
        schema: {
          fields: [
            { name: "typ", type: "string" },
            { name: "sex", type: "string" },
          ],
        },
      },
    },
    source: "enquete-source",
  },
};

const MAP = {
  getLayer: (layerId: string) => LAYERS[layerId],
} as unknown as MapLibreMap;

const featureCollection = (id: string) => ({
  features: [],
  id,
  type: "FeatureCollection",
});

type FetchCall = {
  init: RequestInit;
  respond: (body: unknown, status?: number) => void;
  url: string;
};

/** A fetch whose responses are sent by hand, and which honors `signal`. */
function stubFetch() {
  const calls: FetchCall[] = [];
  const fetchMock = vi.fn(
    (url: string, init: RequestInit) =>
      new Promise<Response>((resolve, reject) => {
        init.signal?.addEventListener("abort", () =>
          reject(init.signal?.reason),
        );
        calls.push({
          init,
          respond: (body, status = 200) =>
            resolve(
              new Response(JSON.stringify(body), {
                status,
                statusText: status === 200 ? "OK" : "Internal Server Error",
              }),
            ),
          url,
        });
      }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return { calls, fetchMock };
}

const getBody = (call: FetchCall | undefined) =>
  JSON.parse(String(call?.init.body));

function setup() {
  return {
    ...stubFetch(),
    ...makeLayerFilters({
      baseUrl: BASE_URL,
      headers: { Authorization: "Bearer token" },
      map: MAP,
    }),
  };
}

beforeEach(() => {
  vi.mocked(setSourceData).mockClear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("setLayerFilters", () => {
  it("posts the compiled where object and sets the response as data", async () => {
    const { calls, setLayerFilters } = setup();

    const done = setLayerFilters({
      layerId: "enquete",
      where: { sex: undefined, typ: { in: ["1", "2"] } },
    });

    expect(calls[0]?.url).toBe("https://api.example.org/maps/enquete");
    expect(calls[0]?.init.method).toBe("POST");
    expect(calls[0]?.init.headers).toEqual({
      Authorization: "Bearer token",
      "Content-Type": "application/json",
    });
    expect(getBody(calls[0])).toEqual(cql.inList("typ", ["1", "2"]));

    calls[0]?.respond(featureCollection("filtered"));
    await done;

    expect(setSourceData).toHaveBeenCalledExactlyOnceWith({
      data: featureCollection("filtered"),
      map: MAP,
      sourceId: "enquete-source",
    });
  });

  it("sends raw filters as they are", async () => {
    const { calls, setLayerFilters } = setup();
    const raw = { args: [{ property: "typ" }, "1"], op: "=" };

    const done = setLayerFilters({ filters: raw, layerId: "enquete" });
    calls[0]?.respond(featureCollection("raw"));
    await done;

    expect(getBody(calls[0])).toEqual(raw);
  });

  it("sends an empty object when nothing is restricted", async () => {
    const { calls, clearLayerFilters, setLayerFilters } = setup();

    const done = Promise.all([
      setLayerFilters({ filters: null, layerId: "enquete" }),
      setLayerFilters({ layerId: "basemap", where: {} }),
    ]);
    for (const call of calls) {
      call.respond(featureCollection("all"));
    }
    await done;

    const cleared = clearLayerFilters("enquete");
    calls[2]?.respond(featureCollection("all"));
    await cleared;

    expect(calls.map(getBody)).toEqual([{}, {}, {}]);
  });

  it("rejects an unknown property without fetching", async () => {
    const { fetchMock, setLayerFilters } = setup();

    await expect(
      setLayerFilters({
        layerId: "enquete",
        where: { age: { eq: "1" }, tpy: { eq: "1" }, typ: { eq: "1" } },
      }),
    ).rejects.toThrow(
      'Unknown properties "age", "tpy" on layer "enquete". Filters use the raw resource column names. Available: typ, sex.',
    );
    await expect(
      setLayerFilters({ filters: cql.eq("tpy", "1"), layerId: "enquete" }),
    ).rejects.toThrow('Unknown property "tpy"');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("skips the property check when the layer has no resource schema", async () => {
    const { calls, setLayerFilters } = setup();

    const done = setLayerFilters({
      filters: cql.eq("anything", "1"),
      layerId: "basemap",
    });
    calls[0]?.respond(featureCollection("basemap"));

    await expect(done).resolves.toBeUndefined();
  });

  it("rejects an unknown layer", async () => {
    const { fetchMock, setLayerFilters } = setup();

    await expect(
      setLayerFilters({ layerId: "nope", where: {} }),
    ).rejects.toThrow("Layer nope doesn't exist.");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("keeps the current data when the backend fails", async () => {
    const { calls, setLayerFilters } = setup();

    const done = setLayerFilters({ layerId: "enquete", where: {} });
    calls[0]?.respond({ detail: "boom" }, 500);

    await expect(done).rejects.toThrow(
      '[FILTERS] Fetching the filtered data of layer "enquete" failed: 500 Internal Server Error - {"detail":"boom"}',
    );
    expect(setSourceData).not.toHaveBeenCalled();
  });

  it("applies the latest call when calls overlap", async () => {
    const { calls, setLayerFilters } = setup();

    const first = setLayerFilters({
      layerId: "enquete",
      where: { typ: { eq: "1" } },
    });
    const second = setLayerFilters({
      layerId: "enquete",
      where: { typ: { eq: "2" } },
    });

    await expect(first).rejects.toMatchObject({ name: "AbortError" });
    calls[1]?.respond(featureCollection("second"));
    await second;

    expect(setSourceData).toHaveBeenCalledExactlyOnceWith(
      expect.objectContaining({ data: featureCollection("second") }),
    );
  });

  it("drops a response that arrived just before a newer call", async () => {
    const { calls, setLayerFilters } = setup();

    const first = setLayerFilters({ layerId: "enquete", where: {} });
    // The response is in, but its body is still being read…
    calls[0]?.respond(featureCollection("first"));
    // …when a newer call supersedes it.
    const second = setLayerFilters({ layerId: "enquete", where: {} });

    await expect(first).rejects.toMatchObject({ name: "AbortError" });
    calls[1]?.respond(featureCollection("second"));
    await second;

    expect(setSourceData).toHaveBeenCalledExactlyOnceWith(
      expect.objectContaining({ data: featureCollection("second") }),
    );
  });

  it("does not abort the calls of other layers", async () => {
    const { calls, setLayerFilters } = setup();

    const enquete = setLayerFilters({ layerId: "enquete", where: {} });
    const basemap = setLayerFilters({ layerId: "basemap", where: {} });
    calls[0]?.respond(featureCollection("enquete"));
    calls[1]?.respond(featureCollection("basemap"));

    await expect(Promise.all([enquete, basemap])).resolves.toBeDefined();
    expect(setSourceData).toHaveBeenCalledTimes(2);
  });

  it("type-checks layers, properties and values when given the layer schemas", () => {
    const { setLayerFilters } = makeLayerFilters<{
      enquete: { sex: string; typ: "0" | "1" | "2" };
    }>({ baseUrl: BASE_URL, map: MAP });

    // Never called: only the types are under test.
    const typeChecks = () => {
      setLayerFilters({ layerId: "enquete", where: { typ: { in: ["1"] } } });
      // @ts-expect-error unknown layer
      setLayerFilters({ layerId: "enqute", where: {} });
      // @ts-expect-error "3" is not a value of typ
      setLayerFilters({ layerId: "enquete", where: { typ: { in: ["3"] } } });
      // @ts-expect-error unknown property
      setLayerFilters({ layerId: "enquete", where: { tpy: { eq: "1" } } });
      // @ts-expect-error where and filters are mutually exclusive
      setLayerFilters({
        filters: null,
        layerId: "enquete",
        where: {},
      });
    };

    expect(typeChecks).toBeTypeOf("function");
  });
});
