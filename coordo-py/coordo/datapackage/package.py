# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import Iterable, Optional

import duckdb
import geopandas as gpd
import pandas as pd
import pyarrow as pa
import pydantic
import sqlalchemy as sa
from dplib import models
from dplib.models import (
    Contributor,
    License,
    Source,
)
from dplib.models import (
    ForeignKeyReference as ForeignKeyReference,
)
from dplib.plugins.sql.models import SqlSchema
from pygeofilter.ast import AstType

from coordo.sql.builder import build_query, compile_query
from coordo.sql.helpers import load_conn

from ..helpers import safe
from .resource import Resource

field_adapter = pydantic.TypeAdapter(models.IField)


def Field(**kwargs):
    return field_adapter.validate_python(kwargs)


def handle_path(path: str | list[str]) -> str:
    assert isinstance(path, str), "Multi-path resources are not yet supported"
    return path


class DataPackage(pydantic.BaseModel):
    id: Optional[str] = None
    name: str = pydantic.Field(pattern=r"^[a-z0-9._-]+$")
    resources: list[Resource] = []
    title: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    version: Optional[str] = None
    licenses: list[License] = []
    sources: list[Source] = []
    contributors: list[Contributor] = []
    keywords: list[str] = []
    image: Optional[str] = None
    created: Optional[str] = None

    _basepath: Path

    def model_post_init(self, context):
        self._basepath = context["_basepath"]
        for resource in self.resources:
            resource._package = self

    @classmethod
    def from_path(cls, path: Path) -> "DataPackage":
        if path.is_dir() or not path.exists():
            path = path / "datapackage.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            print(f"Loading package from {path}")
            return cls.model_validate_json(
                path.read_bytes(),
                context={"_basepath": path.parent},
            )
        else:
            print(f"Creating new package at {path}")
            return cls.model_validate(
                {"name": path.parent.name},
                context={"_basepath": path.parent},
            )

    def save(self):
        Path(self._basepath, "datapackage.json").write_text(
            self.model_dump_json(
                exclude_none=True,
                exclude_defaults=True,
                indent=2,
                round_trip=True,
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
                    assert fk.reference.resource != name, (
                        f"Can't remove the resource {name} : {res.name} have a foreign key pointing to this resource."
                    )
        if resource.path:
            path = handle_path(resource.path)
            Path(self._basepath / path).unlink()
        self.resources = [res for res in self.resources if res.name != name]

    def add_resource(self, resource: Resource) -> None:
        if any(res.name == resource.name for res in self.resources):
            raise ValueError(
                f"A resource named {resource.name} already exists in package {self.name}."
            )
        resource._package = self
        self.resources.append(resource)

    def get_resource(self, name: str) -> Resource:
        resource = next(res for res in self.resources if res.name == name)
        assert resource is not None, f"Resource {name} not found."
        return resource

    def write_resource(self, resource_name: str, it: Iterable[dict]):
        pass
        # resource = self.get_resource(name=resource_name)
        # schema = resource.get_schema()

    def prepare_db(self) -> tuple[duckdb.DuckDBPyConnection, sa.MetaData]:
        conn = load_conn()

        metadata = sa.MetaData()

        for resource in self.resources:
            if resource.path and resource.schema:
                SqlSchema.from_dp(
                    resource.schema,
                    table_name=resource.name,
                ).table.to_metadata(metadata)

                resource.load_table(conn)

        return conn, metadata

    def read_resource(
        self,
        resource_name: str,
        columns: dict[str, AstType] | None = None,
        filter: AstType | None = None,
        groupby: list[str] | None = None,
    ) -> pd.DataFrame:
        conn, metadata = self.prepare_db()
        query = build_query(metadata, resource_name, columns, filter, groupby)
        query_str = compile_query(query)
        relation = conn.sql(query_str)
        table: pa.Table = relation.arrow().read_all()
        conn.close()

        if any(col[1].id == "geometry" for col in relation.description):
            df = gpd.GeoDataFrame.from_arrow(
                table,
                to_pandas_kwargs={"maps_as_pydicts": "strict"},
            )
        else:
            df = table.to_df()

        # Convert numpy arrays to python lists so the dataframe is JSON-serializable
        list_cols = [
            field.name for field in table.schema if pa.types.is_list(field.type)
        ]
        for col in list_cols:
            df[col] = df[col].apply(lambda x: x.tolist() if x is not None else None)

        return df
