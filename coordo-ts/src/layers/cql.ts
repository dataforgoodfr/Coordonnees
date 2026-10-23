/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

/**
 * Builders for the CQL2-JSON filters sent by `setLayerFilters`.
 *
 * The backend (coordo-py) parses them with pygeofilter and applies them as a
 * SQL `WHERE` on the layer's resource, before any `groupby` / `columns`. So
 * properties are the **raw resource column names**, not the aliases defined in
 * the layer `columns`.
 *
 * @see https://docs.ogc.org/is/21-065r2/21-065r2.html (CQL2)
 */

/** A value a property can be compared to. */
export type CqlScalar = string | number | boolean;

/** Reference to a resource column. */
export type CqlProperty = { property: string };

type CqlComparisonOperator = "=" | "<>" | "<" | "<=" | ">" | ">=";

/** A filter expression, as produced by the builders. */
export type CqlExpression =
  | { args: CqlExpression[]; op: "and" | "or" }
  | { args: [CqlExpression]; op: "not" }
  | { args: [CqlProperty, CqlScalar]; op: CqlComparisonOperator }
  | { args: [CqlProperty, string]; op: "like" }
  | { args: [CqlProperty, CqlScalar[]]; op: "in" }
  // pygeofilter reads the bounds as a nested pair, not as two arguments
  | { args: [CqlProperty, [CqlScalar, CqlScalar]]; op: "between" }
  | { args: [CqlProperty]; op: "isNull" };

/**
 * Any CQL2-JSON filter, for what the builders don't cover (spatial or temporal
 * predicates, functions…). Escape hatch: it is not checked beyond its shape.
 */
export type RawCqlFilter = { args: unknown[]; op: string };

/** Filterable properties of one layer, with the type of their values. */
export type LayerProperties = Record<string, CqlScalar>;

/**
 * Filterable properties of every layer, keyed by layer id. Pass it to
 * `createMap` to type-check `setLayerFilters`.
 *
 * @example
 * type Layers = {
 *   enquete: { coh: string; typ: "0" | "1" | "2" };
 * };
 * const mapApi = createMap<Layers>("#map", styleUrl);
 */
export type LayerSchemas = Record<string, LayerProperties>;

type PropertyName<P> = Extract<keyof P, string>;

/**
 * The builder functions, typed against the properties `P` of a layer.
 *
 * `and` and `or` skip `undefined` conditions, so optional filters compose
 * without branching. Both return `undefined`, meaning "no restriction", when no
 * condition is left.
 */
export type CqlBuilder<P extends LayerProperties = LayerProperties> = {
  and(
    ...conditions: Array<CqlExpression | undefined>
  ): CqlExpression | undefined;
  /** Inclusive on both bounds. */
  between<K extends PropertyName<P>>(
    property: K,
    lower: P[K],
    upper: P[K],
  ): CqlExpression;
  eq<K extends PropertyName<P>>(property: K, value: P[K]): CqlExpression;
  gt<K extends PropertyName<P>>(property: K, value: P[K]): CqlExpression;
  gte<K extends PropertyName<P>>(property: K, value: P[K]): CqlExpression;
  /** An empty list matches nothing, like a checkbox group with no box checked. */
  inList<K extends PropertyName<P>>(
    property: K,
    values: readonly P[K][],
  ): CqlExpression;
  isNull<K extends PropertyName<P>>(property: K): CqlExpression;
  /** `%` matches any sequence of characters. */
  like<K extends PropertyName<P>>(property: K, pattern: string): CqlExpression;
  lt<K extends PropertyName<P>>(property: K, value: P[K]): CqlExpression;
  lte<K extends PropertyName<P>>(property: K, value: P[K]): CqlExpression;
  neq<K extends PropertyName<P>>(property: K, value: P[K]): CqlExpression;
  not(condition: CqlExpression): CqlExpression;
  or(
    ...conditions: Array<CqlExpression | undefined>
  ): CqlExpression | undefined;
};

const comparison =
  (op: CqlComparisonOperator) =>
  (property: string, value: CqlScalar): CqlExpression => ({
    args: [{ property }, value],
    op,
  });

const logical =
  (op: "and" | "or") =>
  (...conditions: Array<CqlExpression | undefined>) => {
    // Nested groups of the same operator are flattened: and(and(a, b), c) is
    // and(a, b, c).
    const args = conditions
      .filter((condition) => condition !== undefined)
      .flatMap((condition) =>
        condition.op === op ? condition.args : [condition],
      );

    if (args.length <= 1) {
      return args[0];
    }
    return { args, op } as CqlExpression;
  };

const BUILDER: CqlBuilder = {
  and: logical("and"),
  between: (property, lower, upper) => ({
    args: [{ property }, [lower, upper]],
    op: "between",
  }),
  eq: comparison("="),
  gt: comparison(">"),
  gte: comparison(">="),
  inList: (property, values) => ({
    args: [{ property }, [...values]],
    op: "in",
  }),
  isNull: (property) => ({ args: [{ property }], op: "isNull" }),
  like: (property, pattern) => ({ args: [{ property }, pattern], op: "like" }),
  lt: comparison("<"),
  lte: comparison("<="),
  neq: comparison("<>"),
  not: (condition) => ({ args: [condition], op: "not" }),
  or: logical("or"),
};

/**
 * Untyped builders: any property name, any scalar value.
 *
 * @example
 * mapApi.setLayerFilters({
 *   layerId: "enquete",
 *   filters: cql.and(
 *     cql.inList("typ", ["1", "2"]),
 *     cql.between("coh", "2022", "2023"),
 *   ),
 * });
 */
export const cql = BUILDER;

/**
 * Builders typed against one layer's properties. Same functions as {@link cql},
 * only the types change.
 *
 * @example
 * const q = createCql<{ typ: "0" | "1" | "2" }>();
 * q.eq("typ", "1"); // ✅
 * q.eq("typ", "3"); // ❌ type error
 */
export function createCql<P extends LayerProperties>() {
  return BUILDER as unknown as CqlBuilder<P>;
}

/* -------------------------------------------------------------------------- */
/*                                 Where object                               */
/* -------------------------------------------------------------------------- */

type WhereOperators<V> = {
  between: readonly [V, V];
  eq: V;
  gt: V;
  gte: V;
  in: readonly V[];
  isNull: boolean;
  like: string;
  lt: V;
  lte: V;
  neq: V;
};

/** Exactly one key of `T`. */
type OneOf<T> = {
  [K in keyof T]: Pick<T, K> & Partial<Record<Exclude<keyof T, K>, never>>;
}[keyof T];

/** A condition on one property: an object with exactly one operator. */
export type WhereCondition<V extends CqlScalar = CqlScalar> = OneOf<
  WhereOperators<V>
>;

/**
 * Conditions keyed by property, ANDed together. An `undefined` condition is
 * skipped, so "no restriction on this property" needs no special handling.
 *
 * @example
 * const where: Where = {
 *   age: undefined,
 *   coh: { between: ["2022", "2023"] },
 *   typ: { in: ["1", "2"] },
 * };
 */
export type Where<P extends LayerProperties = LayerProperties> = {
  [K in PropertyName<P>]?: WhereCondition<P[K]> | undefined;
};

const WHERE_OPERATORS = [
  "between",
  "eq",
  "gt",
  "gte",
  "in",
  "isNull",
  "like",
  "lt",
  "lte",
  "neq",
] as const satisfies ReadonlyArray<keyof WhereOperators<CqlScalar>>;

type WhereOperator = (typeof WHERE_OPERATORS)[number];

const isWhereOperator = (key: string): key is WhereOperator =>
  (WHERE_OPERATORS as readonly string[]).includes(key);

function conditionToCql(property: string, condition: object): CqlExpression {
  const entries = Object.entries(condition).filter(
    ([, value]) => value !== undefined,
  );
  const [operator, value] = entries[0] ?? [];
  if (
    entries.length !== 1 ||
    operator === undefined ||
    !isWhereOperator(operator)
  ) {
    throw new Error(
      `[FILTERS] The condition on "${property}" must have exactly one operator among: ${WHERE_OPERATORS.join(", ")}.`,
    );
  }

  switch (operator) {
    case "between": {
      const [lower, upper] = value as [CqlScalar, CqlScalar];
      return BUILDER.between(property, lower, upper);
    }
    case "in":
      return BUILDER.inList(property, value as CqlScalar[]);
    case "isNull":
      return value
        ? BUILDER.isNull(property)
        : BUILDER.not(BUILDER.isNull(property));
    case "like":
      return BUILDER.like(property, value as string);
    default:
      return BUILDER[operator](property, value as CqlScalar);
  }
}

/**
 * Compile a {@link Where} object into a CQL2 expression, or `undefined` when it
 * restricts nothing.
 *
 * @example
 * whereToCql({ sex: { eq: "2" }, typ: { in: ["1", "2"] } });
 * // { op: "and", args: [{ op: "=", … }, { op: "in", … }] }
 */
export function whereToCql<P extends LayerProperties>(where: Where<P>) {
  return BUILDER.and(
    ...Object.entries(where).map(([property, condition]) =>
      condition === undefined
        ? undefined
        : conditionToCql(property, condition as object),
    ),
  );
}

/**
 * Every property a filter refers to. Walks any JSON, so raw filters are covered
 * too.
 */
export function getCqlProperties(filter: unknown): string[] {
  const properties = new Set<string>();

  const walk = (node: unknown) => {
    if (Array.isArray(node)) {
      node.forEach(walk);
    } else if (node !== null && typeof node === "object") {
      if ("property" in node && typeof node.property === "string") {
        properties.add(node.property);
      }
      Object.values(node).forEach(walk);
    }
  };
  walk(filter);

  return [...properties];
}
