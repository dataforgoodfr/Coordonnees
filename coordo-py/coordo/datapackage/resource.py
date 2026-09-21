# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import logging
from typing import TYPE_CHECKING, Any, Self

import duckdb
import pydantic
from dplib.models import (
    Contributor,
    Dialect,
    ForeignKey,
    ForeignKeyReference,
    License,
    Schema,
    Source,
)
from pydantic import model_validator

from .db_helpers import clean_str, prepare_path

logger = logging.getLogger(__name__)


class Resource(pydantic.BaseModel):
    name: str = pydantic.Field(pattern=r"^[a-z0-9._-]+$")
    type: str | None = None
    path: str
    data: Any | None = None
    dialect: Dialect | str | None = None
    schema: Schema
    title: str | None = None
    description: str | None = None
    format: str | None = None
    mediatype: str | None = None
    encoding: str | None = None
    bytes: int | None = None
    hash: str | None = None
    sources: list[Source] = []
    licenses: list[License] = []
    contributors: list[Contributor] = []

    if TYPE_CHECKING:
        from .package import DataPackage

        _package: "DataPackage | None" = None

    @classmethod
    def create(cls, name: str, schema: Schema) -> Self:
        """
        Create and return a Resource object with the specified schema
        """
        resource_name = clean_str(name)
        logger.info(f"Creating resource '{resource_name}'")
        return cls(
            name=resource_name,
            path=f"{resource_name}.parquet",
            schema=schema,
        )

    @property
    def package(self):
        if not self._package:
            raise AttributeError(
                "This resource is not linked to any package. You can't do some actions."
            )
        return self._package

    def load_table(self, conn: duckdb.DuckDBPyConnection):
        query = f'CREATE VIEW "{self.name}" AS SELECT * FROM {prepare_path(self.package.get_path() / self.path)}'
        conn.execute(query)

    def replace_primary_key(self, fields: list[str]) -> None:
        field_names = {field.name for field in self.schema.fields}
        missing_field = next((field for field in fields if field not in field_names), None)

        if missing_field is not None:
            raise ValueError(
                f"The field {missing_field} is not present in the resource "
                f"{self.name} schema and can't be defined as a primary key"
            )

        self.schema.primaryKey = fields

    def add_foreignkey(
        self, fields: list[str], foreign_fields: list[str], foreign_resource: str
    ) -> None:
        if any(
            fk.reference.resource == foreign_resource for fk in self.schema.foreignKeys
        ):
            raise ValueError(
                f"A foreign key already exists between {self.name} and {foreign_resource}"
            )
        fk = ForeignKey(
            fields=fields,
            reference=ForeignKeyReference(
                fields=foreign_fields,
                resource=None if self.name == foreign_resource else foreign_resource,
            ),
        )
        fk_part_names_str = " & ".join(self.get_fk_names(fk))
        logger.info(f"Adding foreign key {fk_part_names_str}")

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
            assert f in field_names, (
                f"Resource {parent_resource.name} has no field named {f}"
            )
        if fk in self.schema.foreignKeys:
            raise ValueError(
                f"Foreign key {fk_part_names_str} already exists in resource {self.name}"
            )
        self.schema.foreignKeys.append(fk)

    def remove_foreignkey(self, foreign_resource: str) -> None:
        fk = next(
            (
                fk
                for fk in self.schema.foreignKeys
                if fk.reference.resource == foreign_resource
            ),
            None,
        )
        if fk is None:
            raise ValueError(
                f"No foreign key to {foreign_resource} found in resource {self.name}"
            )
        logger.info(f"Removing foreign key to {foreign_resource}")
        self.schema.foreignKeys.remove(fk)

    @model_validator(mode="after")
    def check_data_or_path(self) -> Self:
        provided = [self.data, self.path]
        count = len([f for f in provided if f is not None])
        if count != 1:
            raise ValueError("Exactly one of 'data' or 'path' must be provided.")
        return self

    def has_same_schema_as(self, other: Self) -> bool:
        for attr in vars(self.schema):
            if getattr(self.schema, attr) != getattr(other.schema, attr):
                return False
        return True

    def get_fk_names(self, fk: ForeignKey) -> list[str]:
        return [
            f"'{self.name}.{field}' -> '{fk.reference.resource}.{reference_field}'"
            for field, reference_field in zip(fk.fields, fk.reference.fields)
        ]
