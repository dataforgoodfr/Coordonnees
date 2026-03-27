from pygeofilter.ast import AstType
from pygeofilter.backends.sqlalchemy import to_filter
from sqlalchemy import MetaData, and_, select

from .mapper import FieldMapper
from .parser import to_sql

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


def compile_query(query):
    return str(query.compile(compile_kwargs={"literal_binds": True}))


def build_query(
    metadata: MetaData,
    table_name: str,
    columns: dict[str, AstType] | None = None,
    filter: AstType | None = None,
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
        base_query = query.with_only_columns(*group_cols.values())
        query = base_query.group_by(None)

        for alias, ast in columns.items():
            expr, joins = to_sql(ast, field_map, base_query)
            query = query.add_columns(expr.label(alias))
            for join, on in joins:
                query = query.join(join, on)

    return query
