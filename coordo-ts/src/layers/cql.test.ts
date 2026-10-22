/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

import { describe, expect, it } from "vitest";

import {
  type CqlExpression,
  cql,
  createCql,
  getCqlProperties,
  type Where,
  whereToCql,
} from "./cql";

const TYP_IN = cql.inList("typ", ["1", "2"]);
const SEX_EQ = cql.eq("sex", "2");

describe("cql builders", () => {
  it("builds comparisons", () => {
    expect(cql.eq("typ", "1")).toEqual({
      args: [{ property: "typ" }, "1"],
      op: "=",
    });
    expect(
      [cql.neq, cql.lt, cql.lte, cql.gt, cql.gte].map(
        (build) => build("age", 2).op,
      ),
    ).toEqual(["<>", "<", "<=", ">", ">="]);
  });

  it("nests the bounds of between, as pygeofilter expects", () => {
    expect(cql.between("coh", "2022", "2023")).toEqual({
      args: [{ property: "coh" }, ["2022", "2023"]],
      op: "between",
    });
  });

  it("builds in, like, isNull and not", () => {
    expect(TYP_IN).toEqual({
      args: [{ property: "typ" }, ["1", "2"]],
      op: "in",
    });
    expect(cql.inList("typ", [])).toEqual({
      args: [{ property: "typ" }, []],
      op: "in",
    });
    expect(cql.like("name", "Mak%")).toEqual({
      args: [{ property: "name" }, "Mak%"],
      op: "like",
    });
    expect(cql.not(cql.isNull("coh"))).toEqual({
      args: [{ args: [{ property: "coh" }], op: "isNull" }],
      op: "not",
    });
  });

  it("does not share the values array with the caller", () => {
    const values = ["1"];
    const expression = cql.inList("typ", values);
    values.push("2");

    expect(expression).toEqual(cql.inList("typ", ["1"]));
  });

  describe.each(["and", "or"] as const)("%s", (op) => {
    it("combines conditions", () => {
      expect(cql[op](TYP_IN, SEX_EQ)).toEqual({ args: [TYP_IN, SEX_EQ], op });
    });

    it("skips undefined conditions", () => {
      expect(cql[op](undefined, TYP_IN, undefined, SEX_EQ)).toEqual({
        args: [TYP_IN, SEX_EQ],
        op,
      });
    });

    it("returns a single condition as is", () => {
      expect(cql[op](undefined, TYP_IN)).toBe(TYP_IN);
    });

    it("returns undefined when no condition is left", () => {
      expect(cql[op]()).toBeUndefined();
      expect(cql[op](undefined, undefined)).toBeUndefined();
    });

    it("flattens nested groups of the same operator", () => {
      const nested = cql[op](TYP_IN, SEX_EQ) as CqlExpression;
      const other = cql.eq("age", "1");

      expect(cql[op](nested, other)).toEqual({
        args: [TYP_IN, SEX_EQ, other],
        op,
      });
    });
  });

  it("keeps groups of the other operator nested", () => {
    const either = cql.or(TYP_IN, SEX_EQ) as CqlExpression;

    expect(cql.and(either, cql.eq("age", "1"))).toEqual({
      args: [either, cql.eq("age", "1")],
      op: "and",
    });
  });

  it("types the typed builders without changing them", () => {
    const q = createCql<{ age: number; typ: "0" | "1" | "2" }>();

    expect(q.eq("typ", "1")).toEqual(cql.eq("typ", "1"));
    // @ts-expect-error "3" is not a value of typ
    q.eq("typ", "3");
    // @ts-expect-error unknown property
    q.eq("tpy", "1");
    // @ts-expect-error age is a number
    q.between("age", "1", "2");
  });
});

describe("whereToCql", () => {
  it("compiles each operator", () => {
    expect(whereToCql({ a: { eq: "1" } })).toEqual(cql.eq("a", "1"));
    expect(whereToCql({ a: { neq: "1" } })).toEqual(cql.neq("a", "1"));
    expect(whereToCql({ a: { lt: 1 } })).toEqual(cql.lt("a", 1));
    expect(whereToCql({ a: { lte: 1 } })).toEqual(cql.lte("a", 1));
    expect(whereToCql({ a: { gt: 1 } })).toEqual(cql.gt("a", 1));
    expect(whereToCql({ a: { gte: 1 } })).toEqual(cql.gte("a", 1));
    expect(whereToCql({ a: { in: ["1", "2"] } })).toEqual(
      cql.inList("a", ["1", "2"]),
    );
    expect(whereToCql({ a: { between: [1, 2] } })).toEqual(
      cql.between("a", 1, 2),
    );
    expect(whereToCql({ a: { like: "x%" } })).toEqual(cql.like("a", "x%"));
    expect(whereToCql({ a: { isNull: true } })).toEqual(cql.isNull("a"));
    expect(whereToCql({ a: { isNull: false } })).toEqual(
      cql.not(cql.isNull("a")),
    );
  });

  it("ANDs the properties and skips undefined ones", () => {
    expect(
      whereToCql({
        age: undefined,
        sex: { eq: "2" },
        typ: { in: ["1", "2"] },
      }),
    ).toEqual(cql.and(SEX_EQ, TYP_IN));
  });

  it("returns undefined when nothing is restricted", () => {
    expect(whereToCql({})).toBeUndefined();
    expect(whereToCql({ age: undefined })).toBeUndefined();
  });

  it("throws when a condition does not have exactly one operator", () => {
    const invalid = [
      {},
      { eq: "1", neq: "2" },
      { equals: "1" },
      { eq: undefined },
    ] as unknown as Where[string][];

    for (const condition of invalid) {
      expect(() => whereToCql({ typ: condition })).toThrow(
        /condition on "typ" must have exactly one operator/,
      );
    }
  });

  it("rejects conditions with several operators at the type level", () => {
    // @ts-expect-error a condition has exactly one operator
    const where: Where = { typ: { eq: "1", in: ["2"] } };

    expect(where).toBeDefined();
  });
});

describe("getCqlProperties", () => {
  it("lists every property once, at any depth", () => {
    const filter = cql.and(TYP_IN, cql.or(SEX_EQ, cql.not(cql.isNull("typ"))));

    expect(getCqlProperties(filter).sort()).toEqual(["sex", "typ"]);
  });

  it("walks raw filters too", () => {
    expect(
      getCqlProperties({
        args: [{ property: "geom" }, { coordinates: [0, 0], type: "Point" }],
        op: "s_intersects",
      }),
    ).toEqual(["geom"]);
  });

  it("returns nothing for an empty filter", () => {
    expect(getCqlProperties(undefined)).toEqual([]);
    expect(getCqlProperties(null)).toEqual([]);
  });
});
