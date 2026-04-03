# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pygeofilter.ast import AstType
from pygeofilter.backends.sqlalchemy import to_filter
from sqlalchemy import MetaData, Select, func, select

from .evaluator import to_sql
from .mapper import FieldMapper


def print_query(query):
    print(compile_query(query))


def compile_query(query: Select) -> str:
    return str(query.compile(compile_kwargs={"literal_binds": True}))


def build_query(
    metadata: MetaData,
    table_name: str,
    columns: dict[str, AstType] | None = None,
    filter: AstType | None = None,
    groupby: list[str] | None = None,
) -> Select:
    assert not groupby or columns, "You can't groupby without specifying columns"

    table = metadata.tables[table_name]
    field_map = FieldMapper(table.name, metadata)

    query = select().select_from(table)

    if groupby:
        group_cols = [field_map[col] for col in groupby]
        query = query.group_by(*group_cols).with_only_columns(*group_cols)

    if filter:
        query = query.filter(to_filter(filter, table.columns))

    if columns:
        base_query = query

        for alias, ast in columns.items():
            expr, joins = to_sql(ast, field_map, base_query)
            if groupby:
                query = query.add_columns(func.any_value(expr).label(alias))
            else:
                query = query.add_columns(expr.label(alias))
            for join, on in joins:
                query = query.join(join, on, isouter=True)
    else:
        query = query.with_only_columns(table)

    return query
