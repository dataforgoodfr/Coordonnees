import os
from pathlib import Path
from typing import Mapping

import geoalchemy2
import geopandas as gpd
import sqlalchemy as sa
from pygeofilter.backends.sqlalchemy import to_filter
from pygeofilter.parsers.cql2_json import parse as parse_cql2
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session, declarative_base, relationship
from sqlalchemy_serializer import SerializerMixin

from coordo.datapackage import Package

SA_FIELDS: Mapping[str, type["sa.Column"]] = {
    "integer": sa.Integer,
    "number": sa.Float,
    "range": sa.Integer,
    "string": sa.Text,
    "select one": sa.String,
    "select multiple": sa.String,
    "select one from file": sa.String,
    "select multiple from file": sa.String,
    "select all that apply": sa.String,
    "rank": sa.String,
    "geopoint": geoalchemy2.Geometry(geometry_type="POINT", srid=4326),
    "start-geopoint": geoalchemy2.Geometry(geometry_type="POINT", srid=4326),
    # "geotrace": geoalchemy2.Geometry(geometry_type='LINESTRING'),
    # "geoshape": geoalchemy2.Geometry(geometry_type='POLYGON'),
    "date": sa.Date,
    "time": sa.Time,
    "datetime": sa.DateTime,
    # "photo": sa.LargeBinary,
    # "audio": sa.LargeBinary,
    # "background-audio": sa.LargeBinary,
    # "video": sa.LargeBinary,
    # "file": sa.LargeBinary,
    "barcode": None,
    "hidden": None,
    "xml-external": None,
}

Base = declarative_base()

os.environ["SPATIALITE_LIBRARY_PATH"] = "mod_spatialite"


class SpatialiteSource:
    tables: list[Base]

    def __init__(self, package_path):
        path = Path(package_path)
        package = Package.from_json(path.read_text())
        db_path = path.parent / package.resources[0].path
        self.engine = sa.create_engine(
            f"sqlite:///{db_path}",
            # echo=True,
            plugins=["geoalchemy2"],
        )

        table_fields = {}
        for resource in reversed(package.resources):
            fields = {}
            primaryKeys = (
                resource.schema.primaryKey
                if isinstance(resource.schema.primaryKey, list)
                else [resource.schema.primaryKey]
            )
            for field in resource.schema.fields:
                kwargs = {}
                if field.title:
                    kwargs.update()
                for constraint, value in field.constraints.items():
                    if constraint == "required":
                        kwargs.update(nullable=not value)
                if field.name in primaryKeys:
                    kwargs.update(primary_key=True)
                fields[field.name] = sa.Column(
                    SA_FIELDS[field.type or "string"], **kwargs
                )
            for fk in resource.schema.foreignKeys:
                parent_table = fk.reference["resource"]
                fields[fk.fields[0]] = sa.Column(
                    sa.ForeignKey(f'{parent_table}.{fk.reference["fields"][0]}')
                )
                table_fields[parent_table][resource.name] = relationship(resource.name)
            table_fields[resource.name] = fields

        self.tables = []
        for table_name, fields in table_fields.items():
            self.tables.append(
                type(
                    table_name,
                    (Base, SerializerMixin),
                    {"__tablename__": table_name, **fields},
                )
            )

    def create_tables(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def get_filters(self):
        pass

    def set_filters(self, cql2):
        self.filter_ast = parse_cql2(cql2)

    def read_table(self, table_name):
        table = next(
            table for table in self.tables if table.__tablename__ == table_name
        )
        with Session(self.engine) as sess:
            query = sa.select(table)
            if self.filter_ast:
                mapping = {
                    field.name: getattr(table, field.name)
                    for field in inspect(table).columns
                }
                filter = to_filter(self.filter_ast, mapping)
                query = query.filter(filter)
            rows = [row.to_dict() for row in sess.scalars(query)]
            if rows:
                geom_col = next(
                    name
                    for name, field in table.__table__.columns.items()
                    if isinstance(field.type, geoalchemy2.Geometry)
                )
                return gpd.GeoDataFrame(rows, geometry=geom_col)
            return gpd.GeoDataFrame()


if __name__ == "__main__":
    source = SpatialiteSource("../demo/catalog/inventaire_id/datapackage.json")
    source.set_filters(
        {
            "op": "=",
            "args": [{"property": "cod"}, 3],
        }
    )
    gpd = source.read_table("inventaire_id")
    print(gpd.iloc[0])
