import os
from pathlib import Path
from typing import Iterable, Mapping

import geoalchemy2 as ga
import sqlalchemy as sa
from geoalchemy2.shape import to_shape
from pygeofilter.backends.sqlalchemy import to_filter
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import (
    DeclarativeMeta,
    Mapper,
    Session,
    declarative_base,
    relationship,
    sessionmaker,
)
from sqlalchemy.types import TypeEngine
from sqlalchemy_serializer import SerializerMixin

from .datapackage import DataPackage

SA_FIELDS: Mapping[str, TypeEngine] = {
    "integer": sa.Integer(),
    "number": sa.Float(),
    "range": sa.Integer(),
    "string": sa.Text(),
    "select one": sa.String(),
    "select multiple": sa.String(),
    "select one from file": sa.String(),
    "select multiple from file": sa.String(),
    "select all that apply": sa.String(),
    "rank": sa.String(),
    # Geojson is encoded as a generic geometry but we could maybe do
    # better in the future by scanning the data, idk
    "geojson": ga.Geometry(srid=4326),
    "geopoint": ga.Geometry(geometry_type="POINT", srid=4326),
    "start-geopoint": ga.Geometry(geometry_type="POINT", srid=4326),
    "date": sa.Date(),
    "time": sa.Time(),
    "datetime": sa.DateTime(),
}

os.environ["SPATIALITE_LIBRARY_PATH"] = "mod_spatialite"

# It is assumed here that all geometries are in 4326, so it returns
# valid geojson but this will need an update if we want other CRS
SERIALIZE_TYPES = ((ga.WKBElement, lambda geom: to_shape(geom).__geo_interface__),)


@DataPackage.register("sqlite")
class SpatialitePackage(DataPackage):
    _base: DeclarativeMeta | None = None
    _tables: dict[str, Mapper] | None = None

    @property
    def base(self) -> DeclarativeMeta:
        if self._base is None:
            self._generate_tables()
        return self._base  # type: ignore

    @property
    def tables(self) -> dict[str, Mapper]:
        if self._tables is None:
            self._generate_tables()
        return self._tables

    def _generate_tables(self):
        Base = declarative_base()

        table_fields = {}
        for resource in reversed(self.resources):
            fields = {}
            schema = resource.schema
            primaryKeys = []
            if schema.primaryKey:
                pk = schema.primaryKey
                primaryKeys = pk if isinstance(pk, list) else [pk]
            for field in schema.fields:
                kwargs = {}
                if field.constraints:
                    for constraint, value in field.constraints.model_dump().items():
                        if constraint == "required":
                            kwargs.update(nullable=not value)
                if field.name in primaryKeys:
                    kwargs.update(primary_key=True)
                fields[field.name] = sa.Column(
                    SA_FIELDS[field.type or "string"], **kwargs
                )
            if schema.foreignKeys:
                for fk in resource.schema.foreignKeys:
                    parent_table = fk.reference.resource
                    fields[fk.fields[0]] = sa.Column(
                        sa.ForeignKey(f"{parent_table}.{fk.reference.fields[0]}")
                    )
                    table_fields[parent_table][resource.name] = relationship(
                        resource.name
                    )
            table_fields[resource.name] = fields

        tables = {}
        for table_name, fields in table_fields.items():
            tables[table_name] = type(
                table_name,
                (Base, SerializerMixin),
                {
                    **fields,
                    "__tablename__": table_name,
                    "serialize_types": SERIALIZE_TYPES,
                },
            )

        self._tables = tables
        self._base = Base

    def _get_engine(self):
        db_path = self._path / self.resources[0].path
        return sa.create_engine(
            f"sqlite:///{db_path}",
            plugins=["geoalchemy2"],
        )

    def write_schema(self, path: Path):
        assert (
            len(set(resource.path for resource in self.resources)) == 1
        ), "Can't have resources in multiple databases"
        super().write_schema(path)
        engine = self._get_engine()
        self.base.metadata.drop_all(engine)
        self.base.metadata.create_all(engine)

    def write_data(self, resource_name: str, it: Iterable[dict]):
        Session = sessionmaker(bind=self._get_engine())
        session = Session()
        session.bulk_insert_mappings(self.tables[resource_name], it)
        session.commit()

    def read_data(self, resource_name: str, filters=None):
        table = self.tables[resource_name]
        with Session(self._get_engine()) as sess:
            query = sa.select(table)
            if filters:
                mapping = {
                    field.name: getattr(table, field.name)
                    for field in inspect(table).columns
                }
                filter = to_filter(filters, mapping)
                query = query.filter(filter)
        return (row.to_dict() for row in sess.scalars(query))


if __name__ == "__main__":
    from pygeofilter.parsers.cql2_json import parse

    source = SpatialitePackage.from_path(
        "../demo/catalog/inventaire_id/datapackage.json"
    )
    it = source.read_data(
        "inventaire_id",
        parse(
            {
                "op": "=",
                "args": [{"property": "cod"}, 3],
            }
        ),
    )
