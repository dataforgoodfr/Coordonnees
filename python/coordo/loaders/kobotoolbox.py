from pathlib import Path
from typing import Mapping, TypedDict

import numpy as np
import pandas as pd
from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
from pyxform.xls2json import parse_file_to_json
from shapely.geometry import Point
from sqlalchemy.orm import sessionmaker
from xpyth_parser.parse import Parser

from coordo.datapackage import (
    Category,
    Constraints,
    DateField,
    DatetimeField,
    Field,
    ForeignKey,
    GeopointField,
    IntegerField,
    NumberField,
    Package,
    Resource,
    Schema,
    StringField,
    TimeField,
)
from coordo.loaders.constraint import parser
from coordo.sources.spatialite import SpatialiteSource

METADATA_TYPES = [
    "start",
    "end",
    "today",
    "deviceid",
    "subscriberid",
    "simserial",
    "phonenumber",
    "username",
    "email",
    "audit",
    "calculate",
    "note",
]

IGNORE_TYPES = [
    "note",
    "calculate",
]


DP_FIELDS: Mapping[str, type[Field]] = {
    "integer": IntegerField,
    "decimal": NumberField,
    "range": IntegerField,
    "text": StringField,
    "select one": StringField,
    "select multiple": StringField,
    "select one from file": StringField,
    "select multiple from file": StringField,
    "select all that apply": StringField,
    "rank": StringField,
    "geopoint": GeopointField,
    "start-geopoint": GeopointField,
    # "geotrace": peewee.LineStringField,
    # "geoshape": peewee.PolygonField,
    "date": DateField,
    "time": TimeField,
    "dateTime": DatetimeField,
    # "photo": peewee.ImageField,
    # "audio": peewee.FileField,
    # "background-audio": peewee.FileField,
    # "video": peewee.FileField,
    # "file": peewee.FileField,
    # "barcode": None,
    # "hidden": None,
    # "xml-external": None,
}

CATALOG_PATH = "../demo/catalog"


class Question(TypedDict):
    name: str
    type: str
    children: list["Question"]


PRIMARY_KEY = "id"


class KoboToolboxLoader:
    def load(self, xlsform, xlsdata):
        form = parse_file_to_json(xlsform)
        name = form["id_string"].lower()
        self.package = Package(name=name)
        main_resource = self._create_resource(name)
        self._parse_form(form, main_resource)
        for resource in self.package.resources:
            resource.path = "db.sqlite"
        package_path = Path(CATALOG_PATH) / name / "datapackage.json"
        package_path.write_text(self.package.to_json())

        source = SpatialiteSource(package_path)
        source.create_tables()
        sheets_dict = pd.read_excel(xlsdata, sheet_name=None)
        for i, (sheet_name, sheet) in enumerate(sheets_dict.items()):
            table_name = self.package.name if i == 0 else sheet_name.lower()
            resource = next(r for r in self.package.resources if r.name == table_name)
            model = next(
                table for table in source.tables if table.__tablename__ == table_name
            )
            sheet = sheet.rename(
                columns={"_index": PRIMARY_KEY, "_parent_index": "parent_id"}
            )
            fields = []
            for column in model.__table__.columns:
                if column.name in sheet.columns:
                    if isinstance(column.type, Geometry):
                        sheet[column.name] = (
                            sheet[column.name]
                            .fillna("")
                            .apply(
                                lambda coords: (
                                    from_shape(
                                        Point(
                                            [float(c) for c in coords.split(" ")[:2]]
                                        ),
                                        4326,
                                    )
                                    if coords
                                    else None
                                )
                            )
                        )

                    fields.append(column.name)
                else:
                    print(f"Field {column.name} not found in data")
            sheet = sheet[fields]
            # sheet.columns = [slugify(col).replace("-", "_") for col in sheet.columns]
            # sheet = sheet.rename(columns={"parent": "parent_id"})
            sheet = sheet.replace({np.nan: None})
            Session = sessionmaker(bind=source.engine)
            session = Session()
            session.bulk_insert_mappings(model, sheet.to_dict("index").values())
            session.commit()

    def _create_resource(self, name):
        return Resource(
            name=name,
            path="db.sqlite",
            schema=Schema(
                fields=[IntegerField(name=PRIMARY_KEY)],
                primaryKey=PRIMARY_KEY,
            ),
        )

    def _parse_form(self, form, resource: Resource):
        self._parse_questions(form["children"], resource)
        self.package.resources.append(resource)

    def _parse_questions(self, questions: list[Question], resource: Resource):
        for question in questions:
            qtype = question["type"]
            if qtype in METADATA_TYPES + IGNORE_TYPES:
                print("Skipping :", qtype)
                continue
            if qtype == "group":
                self._parse_questions(question["children"], resource)
                continue
            if qtype == "repeat":
                child_resource = self._create_resource(question["name"].lower())
                child_resource.schema.fields.append(IntegerField(name="parent_id"))
                child_resource.schema.foreignKeys.append(
                    ForeignKey(
                        fields=["parent_id"],
                        reference={"resource": resource.name, "fields": [PRIMARY_KEY]},
                    )
                )
                self._parse_form(question, child_resource)
                continue
            if qtype in DP_FIELDS:
                field = DP_FIELDS[qtype](name=question["name"])
                if "label" in question:
                    field.title = question["label"]
                field.constraints = Constraints(required=False)
                if "bind" in question:
                    bind = question["bind"]
                    if "required" in bind:
                        field.constraints["required"] = bind["required"] == "yes"
                    if "constraint" in bind:
                        range = parser.parse(bind["constraint"])
                        print(range)
                if "choices" in question and isinstance(
                    field, (IntegerField, StringField)
                ):
                    field.categories = [
                        Category(value=choice["name"], label=choice["label"])
                        for choice in question["choices"]
                    ]
                resource.schema.fields.append(field)


if __name__ == "__main__":
    KoboToolboxLoader().load(
        "../demo/data/20250213_Inventaire_ID_QuestionnaireK.xlsx",
        "../demo/data/20251017_Inventaire_ID_Donnees.xlsx",
    )
