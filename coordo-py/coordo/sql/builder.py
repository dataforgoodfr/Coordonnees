from pygeofilter.ast import AstType as Filter
from pygeofilter.backends.sqlalchemy import to_filter
from sqlalchemy import FunctionElement, MetaData, and_, select
from sqlalchemy.sql import visitors

from .mapper import FieldMapper
from .parser import parse

# TODO: automatically create this list from Duckdb
AGG_FUNCS = [
    "sum",
    "avg",
    "max",
    "min",
    "list",
    "count",
    "quantile_cont",
    "st_union_agg",
    "gini",
    "categorical_gini",
]


def compile(query):
    return str(query.compile(compile_kwargs={"literal_binds": True}))


def build_query(
    metadata: MetaData,
    table_name: str,
    columns: dict[str, str] | None = None,
    filter: Filter | None = None,
    groupby: list[str] | None = None,
):
    assert not groupby or columns, "You can't groupby without specifying columns"

    table = metadata.tables[table_name]
    field_map = FieldMapper(table.name, metadata)

    def auto_join(query):
        all_joins = [
            tbl
            for tbl in query.froms
            if tbl != table and tbl in metadata.tables.values()
        ]
        fk_joins = {fk.column.table for tbl in all_joins for fk in tbl.foreign_keys}
        fanout_joins = [j for j in all_joins if j not in fk_joins]

        for join in fanout_joins:
            query = query.join(join, isouter=True)

        return query

    query = select(table).select_from(table)

    group_cols = table.primary_key.columns
    if groupby:
        group_cols = {col: field_map[col] for col in groupby}
        query = query.group_by(*group_cols.values())

    if filter:
        query = query.filter(to_filter(filter, table.columns))

    if columns:
        base_query = query.with_only_columns()
        query = base_query.group_by()

        ctes = []

        def add_expression(query, expr, skip=None):
            def agg_replacer(node):
                nonlocal query
                if isinstance(node, FunctionElement) and node.name in AGG_FUNCS:
                    subquery = base_query

                    if skip is node:
                        return None

                    subquery = add_expression(subquery, node, skip=node)
                    subquery = auto_join(subquery)

                    cte = subquery.cte()
                    ctes.append(cte)

                    return cte.columns[node.name]

            expr = visitors.replacement_traverse(expr, {}, agg_replacer)  # type: ignore
            query = query.add_columns(expr)

            return query

        for alias, expr_str in columns.items():
            expr = parse(expr_str, field_map)
            query = add_expression(query, expr.label(alias))

        # if ctes:
        #     first_cte = ctes[0]
        #     final_from = first_cte

        #     for cte in ctes[1:]:
        #         final_from = final_from.join(
        #             cte,
        #             *(final_from.c[col] == cte.c[col] for col in group_cols.values())
        #         )

        #     print("FINAL_FROM", final_from)
        #     query = query.select_from(final_from)
        if ctes:
            query = select(*ctes)

        query = auto_join(query)

    return query
