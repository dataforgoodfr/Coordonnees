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
    DataPackage,
    Field,
    ForeignKey,
    ForeignKeyReference,
    Resource,
    Schema,
)
from coordo.helpers import safe

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


def load(package: DataPackage, xlsform: Path, xlsdata: Path):
    form = parse_file_to_json(str(xlsform))
    name = cast(str, form["id_string"].lower())
    main_resource = _create_resource(name)
    # _parse_form(package, form, main_resource)
    if xlsdata.suffix == ".xlsx":
        sheets_dict = pd.read_excel(xlsdata, sheet_name=None)
    elif xlsdata.suffix == ".csv":
        # I think this encoding is not the one from Kobo we should verify
        sheets_dict = {
            name: pd.read_csv(
                xlsdata,
                sep=";",
                encoding="windows-1252",
                decimal=",",
            )
        }
    else:
        raise ValueError(f"Unsupported file format: {xlsdata}")
    for i, (sheet_name, sheet) in enumerate(sheets_dict.items()):
        table_name = main_resource.name if i == 0 else sheet_name.lower()
        resource = next(r for r in package.resources if r.name == table_name)
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
        path = Path(package._basepath, table_name + ".parquet")
        geo_cols = [f.name for f in schema.fields if f.type == "geojson"]
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


def _create_resource(name) -> Resource:
    return Resource(
        name=name,
        path=name + ".parquet",
        schema=Schema(
            fields=[Field(name=PRIMARY_KEY, type="integer")],
            primaryKey=[PRIMARY_KEY],
        ),
    )


def _parse_form(pkg: DataPackage, form, resource: Resource):
    _parse_questions(pkg, form["children"], resource)
    pkg.add_resource(resource)


def _parse_questions(pkg, questions: List[Dict[str, Any]], resource: Resource):
    schema = safe(resource, "schema")
    for question in questions:
        qtype = question["type"]
        if qtype in METADATA_TYPES + IGNORE_TYPES:
            print("Skipping :", qtype)
            continue
        if qtype == "group":
            _parse_questions(pkg, question["children"], resource)
            continue
        if qtype == "repeat":
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
            _parse_form(pkg, question, child_resource)
            continue
        if qtype in DP_FIELDS:
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
