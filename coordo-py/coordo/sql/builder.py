from collections import UserDict, defaultdict
from functools import cached_property

from pygeofilter.ast import AstType as Filter
from pygeofilter.backends.sqlalchemy import to_filter
from sqlalchemy import FunctionElement, MetaData, and_, func, select
from sqlalchemy.sql import visitors

from .parser import parse


class FieldDict(UserDict):
    def __setitem__(self, key, item):
        if key in self.data:
            raise KeyError(f"Field {key} is already defined.")
        super().__setitem__(key, item)


class FieldMapper:
    def __init__(self, table_name, metadata):
        self.table = metadata.tables[table_name]
        self.metadata = metadata

    def __getitem__(self, key):
        return self.field_map[key]

    @cached_property
    def field_map(self):
        field_map = FieldDict()

        for col in self.table.columns:
            field_map[col.name] = col

        for tbl in self.metadata.tables.values():
            for fk in tbl.foreign_keys:
                if fk.column.table == self.table:
                    field_map[tbl.name] = FieldMapper(tbl.name, self.metadata)

        for fk in self.table.foreign_keys:
            tbl = fk.column.table
            if self.table == tbl:
                print("Self-referencing foreign keys are not yet supported.")
            else:
                field_map[tbl.name] = FieldMapper(tbl.name, self.metadata)

        return field_map


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
    "categorical_gini",
]


def extract_aggregates(node):
    aggs = []

    def function_visitor(node):
        if node.name in AGG_FUNCS:
            aggs.append(node)

    visitors.traverse(
        node,
        {},
        {"function": function_visitor},
    )
    return aggs


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

    query = select(table).select_from(table)

    group_cols = table.primary_key.columns
    if groupby:
        group_cols = {col: field_map[col] for col in groupby}
        query = query.group_by(*group_cols.values())

    if filter:
        query = query.filter(to_filter(filter, table.columns))

    if columns:
        query = query.with_only_columns(*group_cols.values())
        initial_query = query

        def get_joins(query):
            all_joins = [
                tbl
                for tbl in query.froms
                if tbl != table and tbl in metadata.tables.values()
            ]
            fk_joins = {fk.column.table for tbl in all_joins for fk in tbl.foreign_keys}
            return [j for j in all_joins if j not in fk_joins]

            return query

        def add_expression(query, expr, skip=None):
            def agg_replacer(node):
                nonlocal query
                if isinstance(node, FunctionElement) and node.name in AGG_FUNCS:
                    subquery = initial_query.with_only_columns(*group_cols.values())

                    if skip is node:
                        return None

                    subquery = add_expression(subquery, node, skip=node)

                    cte = subquery.cte()

                    query = query.join(
                        cte,
                        and_(
                            *(
                                col == cte.columns[col_name]
                                for col_name, col in group_cols.items()
                            )
                        ),
                    )

                    if skip is not None:
                        return cte.columns[node.name]
                    return func.any_value(cte.columns[node.name])

            expr = visitors.replacement_traverse(expr, {}, agg_replacer)  # type: ignore
            query = query.add_columns(expr)

            return query

        for alias, expr_str in columns.items():
            expr = parse(expr_str, field_map)
            query = add_expression(query, expr)

        print(query)

    return query
