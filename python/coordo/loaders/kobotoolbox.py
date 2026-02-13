from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from geoalchemy2.shape import from_shape
from pyxform.xls2json import parse_file_to_json
from shapely.geometry import Point

from coordo.datapackage.datapackage import (
    Category,
    Constraints,
    Field,
    ForeignKey,
    Reference,
    Resource,
    Schema,
)
from coordo.datapackage.spatialite import SpatialitePackage
from coordo.loaders.constraint import parse_constraint

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


DP_FIELDS = {
    "integer": "integer",
    "decimal": "number",
    "range": "integer",
    "text": "string",
    "select one": "string",
    "select multiple": "string",
    "select one from file": "string",
    "select multiple from file": "string",
    "select all that apply": "string",
    "rank": "string",
    "geopoint": "geojson",
    "start-geopoint": "geojson",
    # "geotrace": peewee.LineStringField,
    # "geoshape": peewee.PolygonField,
    "date": "date",
    "time": "time",
    "dateTime": "datetime",
    # "photo": peewee.ImageField,
    # "audio": peewee.FileField,
    # "background-audio": peewee.FileField,
    # "video": peewee.FileField,
    # "file": peewee.FileField,
    # "barcode": None,
    # "hidden": None,
    # "xml-external": None,
}


PRIMARY_KEY = "id"


class KoboToolboxLoader:
    def load(self, catalog_path: str, xlsform: str, xlsdata: str):
        form = parse_file_to_json(xlsform)
        name = form["id_string"].lower()
        self.package = SpatialitePackage(name=name, resources=[])
        main_resource = self._create_resource(name)
        self._parse_form(form, main_resource)
        self.package.write_schema(Path(catalog_path) / name)
        sheets_dict = pd.read_excel(xlsdata, sheet_name=None)
        for i, (sheet_name, sheet) in enumerate(sheets_dict.items()):
            table_name = self.package.name if i == 0 else sheet_name.lower()
            resource = next(r for r in self.package.resources if r.name == table_name)
            sheet = sheet.rename(
                columns={"_index": PRIMARY_KEY, "_parent_index": "parent_id"}
            )
            fields = []
            for field in resource.schema.fields:
                if field.name in sheet.columns:
                    if field.type == "geojson":
                        sheet[field.name] = (
                            sheet[field.name]
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

                    fields.append(field.name)
                else:
                    print(f"Field {field.name} not found in data")
            sheet = sheet[fields]
            sheet = sheet.replace({np.nan: None})
            self.package.write_data(resource.name, sheet.to_dict("index").values())

    def _create_resource(self, name) -> Resource:
        return Resource(
            name=name,
            path="db.sqlite",
            format="sqlite",
            schema=Schema(
                fields=[Field(name=PRIMARY_KEY, type="integer")],
                primaryKey=PRIMARY_KEY,
            ),
        )

    def _parse_form(self, form, resource: Resource):
        self._parse_questions(form["children"], resource)
        self.package.resources.append(resource)

    def _parse_questions(self, questions: List[Dict[str, Any]], resource: Resource):
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
                child_resource.schema.fields.append(
                    Field(name="parent_id", type="integer")
                )
                child_resource.schema.foreignKeys = [
                    ForeignKey(
                        fields=["parent_id"],
                        reference=Reference(
                            resource=resource.name,
                            fields=[PRIMARY_KEY],
                        ),
                    )
                ]
                self._parse_form(question, child_resource)
                continue
            if qtype in DP_FIELDS:
                field = Field(name=question["name"], type=DP_FIELDS[qtype])
                if "label" in question:
                    field.title = question["label"]
                constraints = dict(required=False)
                if "bind" in question:
                    bind = question["bind"]
                    if "required" in bind:
                        constraints.update(required=bind["required"] == "yes")
                    if "constraint" in bind:
                        constraint = parse_constraint(bind["constraint"])
                        constraints.update(constraint)
                field.constraints = Constraints.model_validate(constraints)
                if "choices" in question:
                    field.categories = [
                        Category(value=choice["name"], label=choice["label"])
                        for choice in question["choices"]
                    ]

                resource.schema.fields.append(field)


if __name__ == "__main__":
    KoboToolboxLoader().load(
        "../demo/catalog",
        "../demo/data/20250213_Inventaire_ID_QuestionnaireK.xlsx",
        "../demo/data/20251017_Inventaire_ID_Donnees.xlsx",
    )
