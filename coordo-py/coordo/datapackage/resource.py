# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from typing import TYPE_CHECKING, Any, Optional, Self

import duckdb
import pydantic
from dplib.models import Contributor, Dialect, ForeignKey, License, Schema, Source
from pydantic import model_validator

from .db_helpers import prepare_path


class Resource(pydantic.BaseModel):
    name: str = pydantic.Field(pattern=r"^[a-z0-9._-]+$")
    type: Optional[str] = None
    path: str
    data: Optional[Any] = None
    dialect: Optional[Dialect | str] = None
    schema: Schema
    title: Optional[str] = None
    description: Optional[str] = None
    format: Optional[str] = None
    mediatype: Optional[str] = None
    encoding: Optional[str] = None
    bytes: Optional[int] = None
    hash: Optional[str] = None
    sources: list[Source] = []
    licenses: list[License] = []
    contributors: list[Contributor] = []

    if TYPE_CHECKING:
        from .package import DataPackage

        _package: "DataPackage | None" = None

    @property
    def package(self):
        if not self._package:
            raise AttributeError(
                "This resource is not linked to any package. You can't do some actions."
            )
        return self._package

    def load_table(self, conn: duckdb.DuckDBPyConnection):
        # db_fields = tuple(
        #     f'"{field.name}"::{to_db_type(field)} AS "{field.name}"'
        #     for field in self.schema.fields
        # )
        query = f'CREATE VIEW "{self.name}" AS SELECT * FROM {prepare_path(self.package._basepath / self.path)}'
        conn.execute(query)

    def add_foreignkey(self, fk: ForeignKey) -> None:
        if not self._package:
            raise ValueError("You can't add a foreign key to an orphan resource.")
        field_names = [f.name for f in self.schema.fields]
        for f in fk.fields:
            if f not in field_names:
                raise ValueError(f"Resource {self.name} has no field named {f}")
        parent_resource = (
            self._package.get_resource(name=fk.reference.resource)
            if fk.reference.resource
            else self
        )
        field_names = [f.name for f in parent_resource.schema.fields]
        for f in fk.reference.fields:
            assert (
                f in field_names
            ), f"Resource {parent_resource.name} has no field named {f}"
        self.schema.foreignKeys.append(fk)
    
    def remove_foreignkey(self, fk: ForeignKey) -> None:
        if fk not in self.schema.foreignKeys:
            raise ValueError(f"Foreign key {fk} not found in resource {self.name}")
        self.schema.foreignKeys.remove(fk)
        

    @model_validator(mode="after")
    def check_data_or_path(self) -> Self:
        provided = [self.data, self.path]
        count = len([f for f in provided if f is not None])
        if count != 1:
            raise ValueError("Exactly one of 'data' or 'path' must be provided.")
        return self
