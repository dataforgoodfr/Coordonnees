import json
from collections import defaultdict
from functools import cached_property
from pathlib import Path
from typing import Any, Iterable, List, Optional, Union

import duckdb
import geopandas as gpd
import pandas as pd
import pydantic
import sqlalchemy as sa
from dplib import models
from dplib.models import (
    Contributor,
    ForeignKey,
    ForeignKeyReference,
    License,
    Schema,
    Source,
)
from dplib.models.dialect.dialect import Dialect
from dplib.plugins.sql.models import SqlSchema
from pydantic import BaseModel, TypeAdapter
from pygeofilter.ast import AstType as Filter
from pygeofilter.backends.sqlalchemy import to_filter
from sqlalchemy.sql import visitors

from ..helpers import StrictDict, safe
from .sql import parse

field_adapter = TypeAdapter(models.IField)


def Field(**kwargs):
    return field_adapter.validate_python(kwargs)


__all__ = [
    "DataPackage",
    "Resource",
    "Field",
    "Schema",
    "ForeignKey",
    "ForeignKeyReference",
]


def handle_path(path: str | list[str]) -> str:
    assert isinstance(path, str), "Multi-path resources are not yet supported"
    return path


def get_nested_aggregates(node, is_nested=False):
    found = []
    is_agg = hasattr(node, "name") and node.name in [
        "sum",
        "avg",
        "max",
        "min",
        "list",
        "quantile_cont",
    ]
    if is_agg and is_nested:
        found.append(node)
    for child in node.get_children():
        found.extend(get_nested_aggregates(child, is_nested or is_agg))
    return found


class FieldMapper:
    def __init__(self, table_name, metadata):
        self.table = metadata.tables[table_name]
        self.metadata = metadata

    def __getitem__(self, key):
        return self.field_map[key]

    @cached_property
    def field_map(self):
        field_map = StrictDict()

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


class Resource(BaseModel):
    name: str
    type: Optional[str] = None
    path: Optional[Union[str, List[str]]] = None
    data: Optional[Any] = None
    dialect: Optional[Union[Dialect, str]] = None
    schema: Optional[Schema] = None
    title: Optional[str] = None
    description: Optional[str] = None
    format: Optional[str] = None
    mediatype: Optional[str] = None
    encoding: Optional[str] = None
    bytes: Optional[int] = None
    hash: Optional[str] = None
    sources: List[Source] = []
    licenses: List[License] = []
    contributors: List[Contributor] = []


class DataPackage(BaseModel):
    resources: List[Resource] = []
    id: Optional[str] = None
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    version: Optional[str] = None
    licenses: List[License] = []
    sources: List[Source] = []
    contributors: List[Contributor] = []
    keywords: List[str] = []
    image: Optional[str] = None
    created: Optional[str] = None

    basepath: Path = pydantic.Field(exclude=True)

    @classmethod
    def from_path(cls, path: Path) -> "DataPackage":
        if not path.exists():
            path.mkdir(parents=True)
        if path.is_dir():
            path = path / "datapackage.json"
        if path.exists():
            print(f"Loading package from {path}")
            return cls.model_validate(
                {
                    **json.loads(path.read_text()),
                    "basepath": path.parent,
                }
            )
        else:
            print(f"Creating new package at {path}")
            return cls(name=path.name, basepath=path.parent)

    def save(self):
        for resource in self.resources:
            resource = self.validate_resource(resource)
        (self.basepath / "datapackage.json").write_text(
            self.model_dump_json(
                exclude_none=True,
                exclude_defaults=True,
                indent=2,
            )
        )

    def remove_resource(self, name: str) -> None:
        resource = self.get_resource(name=name)
        for res in self.resources:
            if res.name == name:
                continue
            sm = safe(res, "schema")
            if sm.foreignKeys:
                for fk in sm.foreignKeys:
                    assert (
                        fk.reference.resource != name
                    ), f"Can't remove the resource {name} : {res.name} have a foreign key pointing to this resource."
        if resource.path:
            path = handle_path(resource.path)
            (self.basepath / path).unlink()
        self.resources = [res for res in self.resources if res.name != name]

    def add_resource(self, resource: Resource) -> None:
        assert (
            resource.path or resource.data
        ), "Please provide either path or data to create a resource"
        assert all(
            res.name != resource.name for res in self.resources
        ), f"A resource named {resource.name} already exists."
        self.resources.append(resource)

    def validate_resource(self, resource: str | Resource) -> Resource:
        if isinstance(resource, str):
            resource = self.get_resource(name=resource)
        if not resource.data:
            p = handle_path(resource.path)  # type: ignore
            parsed = self.basepath / p
            assert parsed.exists(), f"File {parsed} doesn't exist"
        return resource

    def add_foreignkey(self, resource_name: str, fk: ForeignKey) -> None:
        resource = self.get_resource(name=resource_name)
        schema = safe(resource, "schema")
        field_names = [f.name for f in schema.fields]
        for f in fk.fields:
            assert f in field_names, f"Resource {resource_name} has no field named {f}"
        parent_resource = (
            self.get_resource(name=fk.reference.resource)
            if fk.reference.resource
            else resource  # self-referencing
        )
        field_names = [f.name for f in safe(parent_resource, "schema").fields]
        for f in fk.reference.fields:
            assert (
                f in field_names
            ), f"Resource {parent_resource.name} has no field named {f}"
        schema.foreignKeys.append(fk)

    def get_resource(self, name: str) -> Resource:
        resource = next(res for res in self.resources if res.name == name)
        assert resource is not None, f"Resource {name} not found."
        return resource

    def write_resource(self, resource_name: str, it: Iterable[dict]):
        pass
        # resource = self.get_resource(name=resource_name)
        # schema = resource.get_schema()

    # This function loads a resource and recursively load all the associated
    # resources (reverse and foreign keys) into DuckDB
    def load_resource(
        self,
        conn: duckdb.DuckDBPyConnection,
        metadata: sa.MetaData,
        resource: Resource | str,
    ):
        if isinstance(resource, str):
            resource = self.get_resource(resource)

        if resource.name in metadata.tables:
            return

        SqlSchema.from_dp(
            safe(resource, "schema"),
            table_name=resource.name,
        ).table.to_metadata(metadata)

        for res in self.resources:
            if res is resource:
                continue
            sm = safe(res, "schema")
            if sm.foreignKeys:
                for fk in sm.foreignKeys:
                    if fk.reference.resource == resource.name:
                        self.load_resource(conn, metadata, res)

        schema = safe(resource, "schema")
        for fk in schema.foreignKeys:
            if fk.reference.resource:
                self.load_resource(conn, metadata, fk.reference.resource)

        path = self.basepath / safe(resource, "path")
        parsed = Path(path)
        if parsed.suffix == ".geojson":
            conn.execute(
                f'CREATE TABLE "{resource.name}" AS SELECT * FROM ST_Read("{path}")'
            )
        else:
            conn.execute(f'CREATE TABLE "{resource.name}" AS SELECT * FROM "{path}"')

    def read_resource(
        self,
        resource_name: str,
        filter: Filter | None = None,
        groupby: list[str] | None = None,
        columns: dict[str, str] | None = None,
    ) -> pd.DataFrame:
        assert not groupby or columns, "You can't groupby without specifying columns"
        conn = duckdb.connect()
        conn.install_extension("SPATIAL")
        conn.load_extension("SPATIAL")
        conn.execute((Path(__file__).parent / "macros.sql").read_text())

        metadata = sa.MetaData()
        self.load_resource(conn, metadata, resource_name)

        table = metadata.tables[resource_name]
        field_map = FieldMapper(table.name, metadata)

        def get_joins(expr, return_fks):
            if not hasattr(expr, "froms"):
                expr = sa.select(expr)
            external_joins = [
                tbl
                for tbl in expr.froms
                if tbl != table and tbl in metadata.tables.values()
            ]
            if not return_fks:
                fk_joins = {
                    fk.column.table for tbl in external_joins for fk in tbl.foreign_keys
                }
                return [j for j in external_joins if j not in fk_joins]
            return external_joins

        def join_subqueries(query, subqueries):
            for subquery in subqueries:
                query = query.join(
                    subquery,
                    sa.and_(
                        *(
                            getattr(table.columns, col_name)
                            == getattr(subquery.columns, col_name)
                            for col_name in group_cols.keys()
                        )
                    ),
                )
            return query

        query = sa.select(table).select_from(table)

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
                expr, _ = parse(expr_str, field_map)

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
                        print(j)
                        cte = cte.outerjoin(j)

                    # We join to subqueries if there is any
                    for _, _, subqueries in expr_list:
                        cte = join_subqueries(cte, subqueries)
                    cte = cte.cte(f"{join}_cte")

                    # Then we join the CTE to the main query
                    query = query.join(
                        cte,
                        sa.and_(
                            *(
                                col == cte.columns[col_name]
                                for col_name, col in group_cols.items()
                            )
                        ),
                    )

                    # And add the columns as references to the CTE
                    for alias, _, _ in expr_list:
                        cols.append(sa.func.any_value(cte.columns[alias]).label(alias))
                else:
                    # if no join needed then we just add the column as-is and join the subqueries to the main query
                    for alias, expr, subqueries in expr_list:
                        cols.append(expr.label(alias))
                        query = join_subqueries(query, subqueries)

            query = query.with_only_columns(
                *group_cols.values(),
                *cols,
            )

        query_str = str(query.compile(compile_kwargs={"literal_binds": True}))
        relation = conn.sql(query_str)
        table = relation.arrow().read_all()
        if any(str(col[1]).startswith("GEOMETRY") for col in relation.description):
            out = gpd.GeoDataFrame.from_arrow(table)
        else:
            out = pd.DataFrame.from_arrow(table)
        conn.close()
        return out
