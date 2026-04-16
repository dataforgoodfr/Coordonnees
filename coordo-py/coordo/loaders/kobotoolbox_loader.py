# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import json
from datetime import date, datetime
from pathlib import Path
from time import time
from typing import Any, Dict, List, cast

import geopandas as gpd
import numpy as np
import pandas as pd
from lark import Lark, Transformer
from pyxform.xls2json import parse_file_to_json
from shapely.geometry import Point

from coordo.datapackage import (
    Field,
    ForeignKey,
    ForeignKeyReference,
    Resource,
    Schema,
)
from coordo.helpers import safe
from coordo.loaders.loader import Loader, ResourceAction

CONSTRAINT_GRAMMAR = r"""
?start: expression
expression: comparison (AND comparison)*
comparison: DOT OP NUMBER
DOT: "."
OP: "<=" | ">=" | "<" | ">"
AND: "and"
%import common.NUMBER
%import common.WS
%ignore WS
"""


class RangeTransformer(Transformer):
    def comparison(self, items):
        op, number = items[1], float(items[2])
        match op:
            case ">=":
                return {"minimum": number}
            case "<=":
                return {"maximum": number}
            case ">":
                return {"exclusiveMinimum": number}
            case "<":
                return {"exclusiveMaximum": number}

    def expression(self, items):
        result = {}
        for item in items:
            if isinstance(item, dict):
                result.update(item)
        return result


constraint_parser = Lark(
    CONSTRAINT_GRAMMAR, parser="lalr", transformer=RangeTransformer()
)


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
    "select all that apply": "list",
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

DTYPES = {
    "string": str,
    "integer": "Int64",
    "number": float,
    "date": date,
    "time": time,
    "datetime": datetime,
}


PRIMARY_KEY = "_id"


def stringify(obj):
    if isinstance(obj, str):
        return obj
    return json.dumps(obj)


def coords_to_point(coords):
    if not pd.isna(coords):
        lat, lon, alt, prec = map(float, coords.split(" "))
        return Point(lon, lat, alt)


def _create_resource(name: str) -> Resource:
    return Resource(
        name=name,
        path=name + ".parquet",
        schema=Schema(
            fields=[Field(name=PRIMARY_KEY, type="integer")],
            primaryKey=[PRIMARY_KEY],
        ),
    )


def create_main_resource(xlsform: Path) -> Resource:
    print(f"Parsing form from {xlsform}")
    form = parse_file_to_json(str(xlsform))
    name = cast(str, form["id_string"].lower())
    return _create_resource(name)


def _parse_questions(
    questions: List[Dict[str, Any]], resource: Resource
) -> list[Resource]:
    """
    Parses questions (list of dictionaries) and adds them to the resource's schema.
    Example of structure of questions:
        [
            {
                'type': 'integer',
                'name': '<name>',
                'label': '<label>',
                'bind': {'required': 'true', 'constraint': '. < 100', 'jr:constraintMsg': '<constraint message>'}
            },
            {
                'type': 'group',
                'name': '<name>',
                'label': '<label>',
                'control': {'appearance': 'field-list'},
                'children': [
                    {'type': 'text', 'name': 'name1', 'label': "Label1", ...},
                    {'type': 'select one', 'name': 'name2', 'label': 'Label2', ...},
                    {'type': 'integer', 'name': 'name3', 'label': 'Label233', ...}
                ]
            }
        ]
    For each question having a 'group' type, parses recursively the children questions.
    """
    parsed_resources: list[Resource] = []

    schema = safe(resource, "schema")
    for question in questions:
        qtype = question["type"]

        if qtype in METADATA_TYPES + IGNORE_TYPES:
            print("Skipping question type:", qtype)

        elif qtype == "group":
            parsed_children_resources = _parse_questions(question["children"], resource)
            parsed_resources += parsed_children_resources

        elif qtype == "repeat":
            child_resource = _create_resource(question["name"].lower())
            schema = safe(child_resource, "schema")
            schema.add_field(Field(name="parent_id", type="integer"))
            schema.foreignKeys = [
                ForeignKey(
                    fields=["parent_id"],
                    reference=ForeignKeyReference(
                        resource=resource.name,
                        fields=[PRIMARY_KEY],
                    ),
                )
            ]
            parsed_resources.append(child_resource)
            # recursively parse questions and get children resources
            parsed_children_resources = _parse_questions(
                question["children"], child_resource
            )
            parsed_resources += parsed_children_resources

        elif qtype in DP_FIELDS:
            kwargs = dict(name=question["name"], type=DP_FIELDS[qtype])
            if "label" in question:
                kwargs["title"] = stringify(question["label"])
            constraints = {"required": False}
            if qtype == "integer":
                constraints["minimum"] = 0
            if qtype == "select all that apply":
                kwargs["itemType"] = "string"
            if "bind" in question:
                bind = question["bind"]
                if "required" in bind:
                    constraints["required"] = bind["required"] == "true"
                if "constraint" in bind:
                    constraint = constraint_parser.parse(bind["constraint"])
                    constraints.update(constraint)  # type: ignore
            kwargs["constraints"] = constraints
            if "choices" in question:
                kwargs["categories"] = [
                    dict(value=choice["name"], label=stringify(choice["label"]))
                    for choice in question["choices"]
                ]
            schema.fields.append(Field(**kwargs))

    return parsed_resources


class KoboToolboxLoader(Loader):
    main_resource: Resource
    sheets: dict[str, pd.DataFrame]
    processed_sheets: dict[str, pd.DataFrame]

    def __init__(
        self,
        package: Path,
        xlsform: Path,
        xlsdata: Path,
        action: ResourceAction,
    ):
        super().__init__(package, action)
        self.xlsform = xlsform
        self.xlsdata = xlsdata

    def extract(self):
        """
        The xlsform is parsed with the pyxform.xls2json.parse_file_to_json function
        while the xlsdata is parsed with pandas read_excel or read_csv functions.
        """
        print(f"Parsing form from {self.xlsform}")
        form = parse_file_to_json(str(self.xlsform))
        name = cast(str, form["id_string"].lower())
        self.main_resource = _create_resource(name)
        # parses questions from JSON form and add resources to the datapackage
        parsed_resources = _parse_questions(form["children"], self.main_resource)
        # NOTE: we must add the main resource first so that foreign keys are resolved correctly
        self.resources = [self.main_resource] + parsed_resources

        print(f"Parsing data from {self.xlsdata}")
        if self.xlsdata.suffix == ".xlsx":
            self.sheets = pd.read_excel(self.xlsdata, sheet_name=None)
        elif self.xlsdata.suffix == ".csv":
            # TODO: I think this encoding is not the one from Kobo we should verify
            self.sheets = {
                self.main_resource.name: pd.read_csv(
                    self.xlsdata,
                    sep=";",
                    encoding="windows-1252",
                    decimal=",",
                )
            }
        else:
            raise ValueError(f"Unsupported file format: {self.xlsdata}")

    def transform(self):
        print("Processing sheets...")
        self.processed_sheets = {}
        for i, (sheet_name, sheet) in enumerate(self.sheets.items()):
            table_name = self.main_resource.name if i == 0 else sheet_name.lower()
            resource = self.dp.get_resource(table_name)
            schema = safe(resource, "schema")
            sheet = (
                sheet.rename(
                    columns={"_parent_index": "parent_id"},
                )
                .convert_dtypes()
                .replace(np.nan, None)
            )
            sheet[PRIMARY_KEY] = sheet.index + 1
            fields = []
            for field in schema.fields:
                if field.name in sheet.columns:
                    if field.type == "geojson":
                        sheet[field.name] = sheet[field.name].apply(coords_to_point)
                    if field.type == "list":
                        sheet[field.name] = sheet[field.name].apply(
                            lambda string: str(string).split()
                        )
                    if field.type in DTYPES:
                        sheet[field.name] = sheet[field.name].astype(DTYPES[field.type])
                else:
                    print(
                        f"Field {field.name} not found in data. Filling with empty values"
                    )
                    sheet[field.name] = ""
                fields.append(field.name)

            sheet = sheet[fields]
            sheet = sheet.replace({np.nan: None})
            self.processed_sheets[table_name] = sheet

    def load(self):
        print("Loading data...")
        for table_name, sheet in self.processed_sheets.items():
            resource = self.dp.get_resource(table_name)
            path = Path(self.dp._basepath, table_name + ".parquet")
            print(f"Saving {table_name!r} to {path}")

            geo_cols = [f.name for f in resource.schema.fields if f.type == "geojson"]
            if geo_cols:
                gdf = gpd.GeoDataFrame(sheet, geometry=geo_cols[0], crs="EPSG:4326")

                gdf.to_parquet(
                    path,
                    schema_version="1.1.0",
                    index=False,
                    write_covering_bbox=True,
                    geometry_encoding="WKB",  # We use this because duckdb can't open geoarrow as geometries
                )
            else:
                sheet.to_parquet(path, index=False)
