# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import json
from datetime import date, datetime
from pathlib import Path
from time import time
from typing import Any, Dict, List, cast, ClassVar
import logging
import shutil

import geopandas as gpd
import numpy as np
import pandas as pd

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
from coordo.loaders import Loader
from coordo.syntax_parsers import constraint_parser

logger = logging.getLogger(__name__)


def stringify(obj):
    if isinstance(obj, str):
        return obj
    return json.dumps(obj)


def coords_to_point(coords):
    if (
        pd.isna(coords)
        or coords is None
        or (isinstance(coords, str) and not coords.strip())
    ):
        return None
    try:
        lat, lon, alt, prec = map(float, str(coords).split(" "))
    except Exception:
        logger.warning(f"Could not convert coords to Point: {coords}")
        return None
    return Point(lon, lat, alt)


class KoboToolboxLoader(Loader):
    PRIMARY_KEY: ClassVar[str] = "_id"

    METADATA_TYPES: ClassVar[list[str]] = [
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
        "note",
    ]

    IGNORE_TYPES: ClassVar[list[str]] = [
        "note",
    ]

    DP_FIELDS: ClassVar[dict[str, str]] = {
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
        "calculate": "string",
        # "photo": peewee.ImageField,
        # "audio": peewee.FileField,
        # "background-audio": peewee.FileField,
        # "video": peewee.FileField,
        # "file": peewee.FileField,
        # "barcode": None,
        # "hidden": None,
        # "xml-external": None,
    }

    DTYPES: ClassVar[dict] = {
        "string": str,
        "integer": "Int64",
        "number": float,
        "date": date,
        "time": time,
        "datetime": datetime,
    }

    package_name: str
    main_resource: Resource

    def __init__(
        self,
        package: Path | str,
        xlsdata: Path | str,
        xlsform: Path | str | None = None,
    ):
        super().__init__(package)
        self.package_name = Path(package).stem
        self.xlsdata = Path(xlsdata)
        if not self.xlsdata.exists():
            raise FileNotFoundError(f"Kobotoolbox data not found: {self.xlsdata}")

        stored_xlsform: Path | None = self.get_stored_xlsform()
        if xlsform:  # str != "" and is not None
            self.xlsform = Path(xlsform)
            if not self.xlsform.exists():
                raise FileNotFoundError(f"Kobotoolbox form not found: {self.xlsform}")
            if stored_xlsform:
                # this is not an error at all in itself (like when we provide the form to remove the existing resources)
                # but it may be important to log it
                logger.warning(
                    f"Stored Kobotoolbox form exists: {self.get_stored_xlsform()}, but a form was provided: {self.xlsform}"
                )
            else:
                logger.info(
                    f"Stored Kobotoolbox form not found, using provided form: {self.xlsform}"
                )
        else:
            if not stored_xlsform:
                raise FileNotFoundError(
                    f"Could not find XLS form at {self.dp.get_path() / (self.package_name + 'form.*')}"
                )
            self.xlsform = stored_xlsform

    def get_stored_xlsform(self) -> Path | None:
        try:
            return list(self.dp.get_path().glob(f"{self.package_name}.form.*"))[0]
        except IndexError:
            return None

    def parse_input(self):
        self.parse_xlsform_and_get_resources()
        self.extract_xlsdata()
        self.get_resources_and_dataframes_match()

    def get_path_to_copied_xlsform(self):
        return

    def load(self):
        for resource in self.resources:
            self.write_to_package(self.dataframes[resource.name], resource)
        # in addition to this, copying the xlsform in the datapackage
        # if we load, it means that we're in the add method
        # therefore self.xlsform is not None
        copied_xlsform = (
            self.dp.get_path() / f"{self.package_name}.form{self.xlsform.suffix}"
        )
        shutil.copy(self.xlsform, copied_xlsform)

    def get_resource_schema(self) -> Schema:
        return Schema(
            fields=[Field(name=self.PRIMARY_KEY, type="integer")],
            primaryKey=[self.PRIMARY_KEY],
        )

    @staticmethod
    def get_form_name(form: dict) -> str:
        return cast(str, form["id_string"].lower())

    def parse_xlsform_and_get_resources(self):
        """
        The xlsform is parsed with the pyxform.xls2json.parse_file_to_json function
        """
        logger.info(f"Parsing form from {self.xlsform}")
        form: dict = parse_file_to_json(str(self.xlsform))
        self.main_resource = Resource.create(
            self.get_form_name(form), self.get_resource_schema()
        )
        # parses questions from JSON form and add resources to the datapackage
        parsed_resources = self.parse_questions(form["children"], self.main_resource)
        # NOTE: we must add the main resource first so that foreign keys are resolved correctly
        self.resources = [self.main_resource] + parsed_resources

    def extract_xlsdata(self):
        """
        The xlsdata is parsed with pandas read_excel or read_csv functions.
        """
        logger.info(f"Parsing data from {self.xlsdata}")
        suffix = self.xlsdata.suffix

        if suffix == ".xlsx":
            table_name_to_df_dict: dict[str, pd.DataFrame] = pd.read_excel(
                self.xlsdata, sheet_name=None
            )
            resource_names = [resource.name for resource in self.resources]

            for i, (sheet_name, df) in enumerate(table_name_to_df_dict.items()):
                table_name = self.main_resource.name if i == 0 else sheet_name.lower()
                if table_name not in resource_names:
                    logger.warning(f"Sheet name '{sheet_name}' not found in resources")
                # store the dataframe in the sheets dictionary
                self.dataframes[table_name] = df

        elif suffix == ".csv":
            # TODO: I think this encoding is not the one from Kobo we should verify
            self.dataframes = {
                self.main_resource.name: pd.read_csv(
                    self.xlsdata,
                    sep=";",
                    encoding="windows-1252",
                    decimal=",",
                )
            }

        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def get_resources_and_dataframes_match(self):
        """
        Removing resources parsed from the form which do not have a corresponding table in data.
        TODO: better handle Kobotoolbox sheet naming to avoid having to perform this check
        """
        table_names = list(self.dataframes.keys())
        valid_resources = []
        for resource in self.resources:
            if resource.name in table_names:
                valid_resources.append(resource)
            else:
                logger.error(
                    f"Could not find resource name '{resource.name}' in parsed tables. Removing resource."
                )
        self.resources = valid_resources

    def get_foreignkey_to(self, parent_resource: Resource) -> ForeignKey:
        return ForeignKey(
            fields=["parent_id"],
            reference=ForeignKeyReference(
                resource=parent_resource.name,
                fields=[self.PRIMARY_KEY],
            ),
        )

    def parse_questions(
        self, questions: List[Dict[str, Any]], resource: Resource
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

            if qtype in self.METADATA_TYPES + self.IGNORE_TYPES:
                logger.info(f"Skipping question type: {qtype}")

            elif qtype == "group":
                parsed_children_resources = self.parse_questions(
                    question["children"], resource
                )
                parsed_resources += parsed_children_resources

            elif qtype == "repeat":
                child_resource = Resource.create(
                    question["name"].lower(), self.get_resource_schema()
                )
                # Use a different variable name to not change the schema used in the for loop
                child_schema = safe(child_resource, "schema")
                child_schema.add_field(Field(name="parent_id", type="integer"))
                child_schema.foreignKeys = [self.get_foreignkey_to(resource)]
                parsed_resources.append(child_resource)
                # recursively parse questions and get children resources
                parsed_children_resources = self.parse_questions(
                    question["children"], child_resource
                )
                parsed_resources += parsed_children_resources

            elif qtype in self.DP_FIELDS:
                kwargs = dict(name=question["name"], type=self.DP_FIELDS[qtype])
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
                        try:
                            constraint = constraint_parser.parse(bind["constraint"])
                            constraints.update(constraint)  # type: ignore
                        # Fallback in case of unsupported constraint syntax
                        except Exception as e:
                            logger.error(
                                f"Error parsing constraint for question {question['name']}: {e}"
                            )
                            constraints.update(
                                {"unknownConstraint": bind["constraint"]}
                            )
                kwargs["constraints"] = constraints
                if "choices" in question:
                    kwargs["categories"] = [
                        dict(value=choice["name"], label=stringify(choice["label"]))
                        for choice in question["choices"]
                    ]
                schema.fields.append(Field(**kwargs))

        return parsed_resources

    def transform(self):
        logger.info("Processing sheets...")
        for name, df in self.dataframes.items():
            resource = self.dp.get_resource(name)
            schema = safe(resource, "schema")

            df = (
                df.rename(
                    columns={"_parent_index": "parent_id"},
                )
                .convert_dtypes()
                .replace(np.nan, None)
            )
            df[self.PRIMARY_KEY] = df.index + 1

            # adapting pandas dtypes to schema field types
            fields = []
            for field in schema.fields:
                if field.name in df.columns:
                    if field.type == "geojson":
                        df[field.name] = df[field.name].apply(coords_to_point)
                    if field.type == "list":
                        df[field.name] = df[field.name].apply(
                            lambda string: str(string).split()
                        )
                    if field.type in self.DTYPES:
                        df[field.name] = df[field.name].astype(self.DTYPES[field.type])
                else:
                    logger.warning(
                        f"Field {field.name} not found in data. Filling with empty values"
                    )
                    df[field.name] = None if field.type == "geojson" else ""

                fields.append(field.name)

            df = df[fields]
            df = df.replace({np.nan: None})

            # if some columns contain geometry data
            # converting the pandas dataframe to a geopandas dataframe
            geo_cols = [
                f.name
                for f in resource.schema.fields
                if f.type == "geojson"
                and f.name in df.columns
                and df[f.name].notna().any()
            ]

            if geo_cols:
                # GeoPandas only supports one active geometry column in a GeoDataFrame.
                # Convert any additional geo columns into WKB strings so parquet export can succeed.
                for col in geo_cols[1:]:
                    df[col] = df[col].apply(
                        lambda geom: geom.wkb if geom is not None else None
                    )

                df = gpd.GeoDataFrame(df, geometry=geo_cols[0], crs="EPSG:4326")

            # storing transformed dataframe
            self.dataframes[name] = df

    def append_data(self, resource_name: str | None = None):
        for resource in self.resources:
            self.append_datafame_to_resource(self.dataframes[resource.name], resource)

    def replace_data(self, resource_name: str | None = None):
        for resource in self.resources:
            self.replace_resource_data_by_dataframe(
                self.dataframes[resource.name], resource
            )
