from collections import UserDict, defaultdict
from functools import cached_property

from pygeofilter.ast import AstType as Filter
from pygeofilter.backends.sqlalchemy import to_filter
from sqlalchemy import MetaData, and_, func, select
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


def get_nested_aggregates(node, is_nested=False):
    found = []
    is_agg = hasattr(node, "name") and node.name in [
        "sum",
        "avg",
        "max",
        "min",
        "list",
        "quantile_cont",
        "st_union_agg",
    ]
    if is_agg and is_nested:
        found.append(node)
    for child in node.get_children():
        found.extend(get_nested_aggregates(child, is_nested or is_agg))
    return found


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

    def get_joins(expr, return_fks):
        if not hasattr(expr, "froms"):
            expr = select(expr)
        external_joins = {
            tbl
            for tbl in expr.froms
            if tbl != table and tbl in metadata.tables.values()
        }
        if not return_fks:
            fk_joins = {
                fk.column.table for tbl in external_joins for fk in tbl.foreign_keys
            }
            return tuple(external_joins - fk_joins)
        return tuple(external_joins)

    def join_subqueries(query, subqueries):
        for subquery in subqueries:
            query = query.join(
                subquery,
                and_(
                    *(
                        getattr(table.columns, col_name)
                        == getattr(subquery.columns, col_name)
                        for col_name in group_cols.keys()
                    )
                ),
            )
        return query

    query = select(table).select_from(table)

    group_cols = table.primary_key.columns
    if groupby:
        group_cols = {col: field_map[col] for col in groupby}
        query = query.group_by(*group_cols.values())

    if filter:
        query = query.filter(to_filter(filter, table.columns))

    if columns:
        cols = []
        initial_query = query

        expr_by_join = defaultdict(list)
        for alias, expr_str in columns.items():
            expr = parse(expr_str, field_map)

            # Since nested aggregates are not supported in SQL, we need to put them in subqueries
            nested_aggregates = get_nested_aggregates(expr)
            subqueries = []
            for agg in nested_aggregates:
                subquery = query.with_only_columns(*group_cols.values(), agg)

                joins = get_joins(subquery, return_fks=False)
                for join in joins:
                    subquery = subquery.outerjoin(join)

                subquery = subquery.subquery()

                # Here we replace the nested aggregates by their reference
                # in the subquery
                def replacer(node):
                    # There is sometimes an error I can't manage to resolve...
                    try:
                        if agg.compare(node):
                            return subquery.columns[agg.name]
                    except Exception:
                        pass

                expr = visitors.replacement_traverse(expr, {}, replacer)  # type: ignore

                subqueries.append(subquery)

            joins = get_joins(expr, return_fks=False)
            assert (
                len(joins) < 2
            ), "Can't join to more than one table because it will duplicate rows"
            join = joins[0] if joins else None
            expr_by_join[join].append((alias, expr, subqueries))

        for join, expr_list in expr_by_join.items():
            if join is not None:
                # If we need to join, then we put the associated expressions
                # into a CTE in order to not modify the main query
                cte_columns = list(group_cols.values())
                for alias, expr, _ in expr_list:
                    cte_columns.append(expr.label(alias))
                cte = initial_query.with_only_columns(*cte_columns)

                for j in get_joins(cte, return_fks=True):
                    cte = cte.outerjoin(j)

                # We join to subqueries if there is any
                for _, _, subqueries in expr_list:
                    cte = join_subqueries(cte, subqueries)
                cte = cte.cte(f"{join}_cte")

                # Then we join the CTE to the main query
                query = query.join(
                    cte,
                    and_(
                        *(
                            col == cte.columns[col_name]
                            for col_name, col in group_cols.items()
                        )
                    ),
                )

                # And add the columns as references to the CTE
                for alias, _, _ in expr_list:
                    cols.append(func.any_value(cte.columns[alias]).label(alias))
            else:
                # if no join needed then we-- Avoid division by zero just add the column as-is and join the subqueries to the main query
                for alias, expr, subqueries in expr_list:
                    cols.append(expr.label(alias))
                    query = join_subqueries(query, subqueries)

        query = query.with_only_columns(
            *group_cols.values(),
            *cols,
        )
    return query
