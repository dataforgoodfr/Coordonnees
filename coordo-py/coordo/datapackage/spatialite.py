import json
import os
from pathlib import Path
from typing import Iterable, Mapping

import geoalchemy2 as ga
import sqlalchemy as sa
import sqlite_sqlean
from geoalchemy2.shape import to_shape
from marshmallow.fields import Decimal
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
from sqlalchemy.sql import visitors
from sqlalchemy.types import TypeEngine

from coordo.datapackage.aggregate import parse

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


def convert_geom(elem):
    if isinstance(elem, ga.WKBElement):
        elem = to_shape(elem).__geo_interface__
    return elem


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

    def _generate_tables(self, ignore_constraints: list[str] = []):
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
                        if (
                            constraint == "required"
                            and constraint not in ignore_constraints
                        ):
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
                (Base,),
                {
                    **fields,
                    "__tablename__": table_name,
                },
            )

        self._tables = tables
        self._base = Base

    def _get_engine(self):
        db_path = self._path / self.resources[0].path
        engine = sa.create_engine(
            f"sqlite:///{db_path}",
            plugins=["geoalchemy2"],
        )

        @sa.event.listens_for(engine, "connect")
        def load_sqlean_stats(dbapi_connection, connection_record):
            dbapi_connection.enable_load_extension(True)
            sqlite_sqlean.load(dbapi_connection, "stats")

        return engine

    def write_schema(self, path: Path, ignore_constraints: list[str] = []):
        assert (
            len(set(resource.path for resource in self.resources)) == 1
        ), "Can't have resources in multiple databases"
        super().write_schema(path)
        engine = self._get_engine()
        self._generate_tables(ignore_constraints)
        self.base.metadata.drop_all(engine)
        self.base.metadata.create_all(engine)

    def write_data(self, resource_name: str, it: Iterable[dict]):
        Session = sessionmaker(bind=self._get_engine())
        session = Session()
        session.bulk_insert_mappings(self.tables[resource_name], it)
        session.commit()

    def read_data(
        self,
        resource_name: str,
        filter=None,
        groupby=[],
        aggregate={},
    ):
        table = self.tables[resource_name]
        field_map = {
            field.name: getattr(table, field.name) for field in inspect(table).columns
        }
        with Session(self._get_engine()) as sess:
            query = sa.select(table)
            if filter:
                query = query.filter(to_filter(filter, field_map))
            cols = []
            group_cols = {col: field_map[col] for col in groupby}
            query = query.group_by(*group_cols.values())
            cols.extend(group_cols.values())
            if aggregate:
                agg_cols = []
                joins = set()
                subqueries = []
                for alias, agg in aggregate.items():
                    agg_query, agg_joins, agg_subqueries = parse(agg, table)
                    agg_cols.append(agg_query.label(alias))
                    joins.update(agg_joins)
                    for subq in agg_subqueries:
                        if any(q.compare(subq) for q in subqueries):
                            continue
                        subqueries.append(subq)
                query = query.with_only_columns(
                    *group_cols.values(),
                    *agg_cols,
                )
                for join in joins:
                    query = query.join(join, isouter=True)
                if subqueries:
                    subquery = sa.select(
                        *group_cols.values(),
                        *subqueries,
                    ).group_by(*group_cols)
                    for join in joins:
                        subquery = subquery.join(join, isouter=True)
                    subquery = subquery.subquery()

                    def replacer(node):
                        for subq in subqueries:
                            # There is something an error I can't manage to resolve...
                            try:
                                if subq.compare(node):
                                    return subquery.c[subq.name]
                            except:
                                pass

                    query = visitors.replacement_traverse(query, {}, replacer)
                    query = query.join(
                        subquery,
                        sa.and_(
                            col == getattr(subquery.c, col_name)
                            for col_name, col in group_cols.items()
                        ),
                    )
                print(query)

        return (
            {k: convert_geom(v) for k, v in row._mapping.items()}
            for row in sess.execute(query)
        )


if __name__ == "__main__":
    source = SpatialitePackage.from_path(
        "../demo/catalog/inventaire_id/datapackage.json"
    )
    # it = source.read_data(
    #     "inventaire_id",
    #     groupby=["for", "cod"],
    #     aggregate={
    #         # "geom": "centroid(gps)",
    #         "richness": "count(ind.ess_arb)",
    #         "dominant_height": "avg(ind.haut if ind.haut > percentile(ind.haut, 80))",
    #         "soil_structure": "(ep1*not1 + ep2*not2 + ep3*not3 + ep4*not4 + ep5*not5) / 250",
    #         "count1": "sum(tsbf_001.tax1_tsbf)",
    #     },
    # )
    source = SpatialitePackage.from_path(
        "../demo/catalog/enquete_menage_cdf/datapackage.json"
    )
    it = source.read_data(
        "enquete_menage_cdf",
        groupby=["admi2"],
        aggregate={
            "bois_coll_count": "avg(1 if 'bois_coll' in ener else 0) * 100",
            "dech_veg_count": "avg(1 if 'dech_veg' in ener else 0) * 100",
            "conso": "sum((feu_qte * 1 * feu_jrs + char_qte * 1 * char_jrs) / hab * 12 / 600)",
        },
    )

    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)

    print(json.dumps(list(it), indent=2, default=decimal_default))
