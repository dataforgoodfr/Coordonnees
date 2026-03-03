import json
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
from dplib.models.field.datatypes.geojson import GeojsonField
from dplib.plugins.sql.models import SqlSchema
from pydantic import BaseModel, TypeAdapter
from pygeofilter.ast import AstType as Filter
from pygeofilter.backends.sqlalchemy import to_filter
from sqlalchemy.sql import visitors

from ..helpers import safe
from .aggregate import parse

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
    def from_path(cls, path: Path):
        if path.is_dir():
            path = path / "datapackage.json"
        return cls.model_validate(
            {
                **json.loads(path.read_text()),
                "basepath": path.parent,
            }
        )

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
            assert parsed.exists(), f"File {p} doesn't exist"
            if parsed.suffix == ".geojson":
                # When loading a geojson into duckdb a geom field is automatically
                # created so we add it there
                safe(resource, "schema").fields.append(GeojsonField(name="geom"))
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

    def read_resource(
        self,
        resource_name: str,
        filter: Filter | None = None,
        groupby: list[str] | None = None,
        aggregate: dict[str, str] | None = None,
    ) -> pd.DataFrame | gpd.GeoDataFrame:
        resource = self.get_resource(name=resource_name)
        schema = safe(resource, "schema")

        resources_to_load: List[Resource] = [resource]

        reverse_fks = {}
        for res in self.resources:
            if res is resource:
                continue
            sm = safe(res, "schema")
            if sm.foreignKeys:
                for fk in sm.foreignKeys:
                    if fk.reference.resource == resource.name:
                        reverse_fks[res.name] = {
                            from_: to
                            for from_, to in zip(fk.fields, fk.reference.fields)
                        }
                        resources_to_load.append(res)
        fks = []
        for fk in schema.foreignKeys:
            reverse_fks = {}
            if fk.reference.resource:
                res = self.get_resource(name=fk.reference.resource)
                fks.append(res.name)
                resources_to_load.append(res)
            else:
                fks.append(resource.name)

        conn = duckdb.connect()
        conn.load_extension("SPATIAL")
        conn.sql("CALL register_geoarrow_extensions()")

        metadata = sa.MetaData()
        for res in resources_to_load:
            SqlSchema.from_dp(
                safe(res, "schema"),
                table_name=res.name,
            ).table.to_metadata(metadata)
            path = self.basepath / safe(res, "path")
            if path:
                parsed = Path(path)
                table_name = parsed.stem
                if parsed.suffix == ".geojson":
                    conn.execute(
                        f'CREATE TABLE "{table_name}" AS SELECT * FROM ST_Read("{path}")'
                    )
                else:
                    conn.execute(
                        f'CREATE TABLE "{table_name}" AS SELECT * FROM "{path}"'
                    )
        table = metadata.tables[resource_name]
        field_map = {}
        for col in table.c:
            field_map[col.name] = col
        for tbl in reverse_fks:
            field_map[tbl] = metadata.tables[tbl]
        for tbl in fks:
            if table == tbl:
                # if self-referencing we must alias it
                field_map[tbl] = metadata.tables[tbl].alias()
            else:
                field_map[tbl] = metadata.tables[tbl]
        query = sa.select(table)
        if filter:
            query = query.filter(to_filter(filter, field_map))
        primary_keys = (
            schema.primaryKey
            if isinstance(schema.primaryKey, list)
            else [schema.primaryKey]
        )
        group_cols = {pk: field_map[pk] for pk in primary_keys}
        if groupby:
            group_cols = {col: field_map[col] for col in groupby}
            query = query.group_by(*group_cols.values())
        if aggregate:
            agg_cols = []
            joins = set()
            subqueries = []
            for alias, agg in aggregate.items():
                agg_query, agg_joins, agg_subqueries = parse(agg, field_map)
                agg_cols.append(agg_query.label(alias))
                joins.update(agg_joins)
                for subq in agg_subqueries:
                    if any(q.compare(subq) for q in subqueries):
                        # deduplicating subqueries
                        continue
                    subqueries.append(subq)
            query = query.with_only_columns(
                *group_cols.values(),
                *agg_cols,
            )
            for join in joins:
                query = query.join(
                    join,
                    isouter=True,
                )
            if subqueries:
                subquery = sa.select(
                    *group_cols.values(),
                    *subqueries,
                ).group_by(*group_cols.values())
                for join in joins:
                    subquery = subquery.join(join, isouter=True)
                subquery = subquery.subquery()

                def replacer(node):
                    for subq in subqueries:
                        # There is sometimes an error I can't manage to resolve...
                        try:
                            if subq.compare(node):
                                return subquery.c[subq.name]
                        except Exception:
                            pass

                query = visitors.replacement_traverse(query, {}, replacer)  # type: ignore
                query = query.join(
                    subquery,
                    sa.and_(
                        *(
                            col == getattr(subquery.c, col_name)
                            for col_name, col in group_cols.items()
                        )
                    ),
                )
        relation = conn.sql(str(query.compile(compile_kwargs={"literal_binds": True})))
        if any(col[1] == "GEOMETRY" for col in relation.description):
            out = gpd.GeoDataFrame.from_arrow(relation)
        else:
            out = pd.DataFrame.from_arrow(relation)
        conn.close()
        return out
