# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from abc import ABC, abstractmethod
from typing import ClassVar
from pathlib import Path
from enum import Enum
import pandas as pd
import geopandas as gpd
import logging
import duckdb
import re

from ..datapackage import DataPackage, Resource, Schema
from ..sql.helpers import load_conn


logger = logging.getLogger(__name__)


class Separator(str, Enum):
    COMMA = ","
    SEMICOLON = ";"
    TAB = "\t"
    PIPE = "|"
    DOT = "."


class UpdateMethod(str, Enum):
    APPEND = "append"
    REPLACE = "replace"


def write_parquet(df: pd.DataFrame, path: Path | str):
    if isinstance(df, gpd.GeoDataFrame):
        df.to_parquet(
            path,
            schema_version="1.1.0",
            index=False,
            write_covering_bbox=True,
            geometry_encoding="WKB",  # We use this because duckdb can't open geoarrow as geometries
        )
    elif isinstance(df, pd.DataFrame):
        df.to_parquet(path, index=False)
    else:
        raise TypeError(f"Unknown dataframe type: {type(df)}")


class Loader(ABC):
    _ACCEPTS_TARGET_RESOURCES: ClassVar[bool] = False

    def __init__(self, package: Path):
        self.dp = DataPackage.from_path(package)
        self.resources: list[Resource] = []
        self.dataframes: dict[str, pd.DataFrame | gpd.GeoDataFrame] = {}

    @abstractmethod
    def parse_input(self):
        """
        Extract data and resources from the source and populate the `resources` list.
        """
        raise NotImplementedError()

    def transform(self):
        """
        Apply any necessary transformations to the data before loading it into the staging directory.
        """
        pass

    def load(self):
        for resource in self.resources:
            self.write_to_package(self.dataframes[resource.name], resource)

    def save(self):
        """
        Invoke the package's save method, which updates the datapackage.json file on disk.
        """
        self.dp.save()

    @abstractmethod
    def parse_resource_names(self) -> list[str]:
        """
        Return the names of the resources that could be parsed from the provided input.
        """
        raise NotImplementedError()

    ######################################
    # ADD / REMOVE RESOURCES
    ######################################

    def add(self):
        """
        Extract the corresponding resources to add, transform, and load them into the package.
        """
        self.parse_input()
        for resource in self.resources:
            self.dp.attach_resource(resource)
        self.transform()
        self.load()
        self.save()

    def remove(self):
        """
        Extract the correct resources to remove, then remove them from the package.
        """
        self.parse_input()
        for resource in self.resources:
            self.dp.remove_resource(resource.name)
        self.save()

    @staticmethod
    def remove_one_resource(package: Path, resource_name: str):
        """
        Remove the specified resource from the package.
        """
        dp = DataPackage.from_path(package)
        dp.remove_resource(resource_name)
        dp.save()

    ######################################
    # UPDATE (APPEND / REPLACE)
    ######################################

    def update(self, method: UpdateMethod, resource_name: str | None = None):
        """
        Update the package with the current resources.
        The method is common whether appending or replacing data.
        """
        if resource_name is not None:
            self.check_resource_name_can_be_supplied()
        self.parse_input()
        self.transform()
        match method:
            case UpdateMethod.APPEND:
                self.append_data(resource_name)
            case UpdateMethod.REPLACE:
                self.replace_data(resource_name)
        # NOTE: there is no need to save here
        # as the modifications are done on the data only, not on the schema

    def check_resource_name_can_be_supplied(self):
        if not self._ACCEPTS_TARGET_RESOURCES:
            raise ValueError(
                f"Cannot supply a target resource name with {self.__class__.__name__}"
            )

    @abstractmethod
    def append_data(self, resource_name: str | None = None):
        raise NotImplementedError()

    @abstractmethod
    def replace_data(self, resource_name: str | None = None):
        raise NotImplementedError()

    def append_datafame_to_resource(self, df: pd.DataFrame, resource: Resource):
        logger.info(f"Appending data to resource '{resource.name}'")
        current_df = self.dp.read_resource(resource.name)
        # concatenating current and new data
        new_df = pd.concat([current_df, df], ignore_index=True)
        # saving concatenated data back to the current resource's path
        self.write_to_package(new_df, resource)

    def replace_resource_data_by_dataframe(self, df: pd.DataFrame, resource: Resource):
        logger.info(f"Replacing data in resource '{resource.name}'")
        # saving concatenated data back to the current resource's path
        self.write_to_package(df, resource)

    ######################################
    # DELETE
    ######################################

    def delete(self):
        resource_names = self.parse_resource_names()
        for resouce_name in resource_names:
            resource = self.dp.get_resource(resouce_name)
            df = self.dp.read_resource(resouce_name)
            logger.info(f"Deleting data from resource {resouce_name}")
            empty_df_with_same_schema = df.head(0).copy()
            self.write_to_package(empty_df_with_same_schema, resource)

    @staticmethod
    def delete_one_resource(package: Path, resource_name: str):
        """
        Delete data from a resource.
        """
        dp = DataPackage.from_path(package)
        resource = dp.get_resource(resource_name)
        df = dp.read_resource(resource_name)
        logger.info(f"Deleting data from resource {resource_name}")
        empty_df_with_same_schema = df.head(0).copy()
        target_path = dp.get_path() / resource.path
        logger.info(f"Writing parquet file to package at {target_path}")
        write_parquet(empty_df_with_same_schema, target_path)

    ######################################
    # READ / WRITE PARQUET
    ######################################

    def read_parquet(self, resource: Resource) -> pd.DataFrame:
        target_filename = resource.name + ".parquet"
        target_path = self.dp.get_path() / target_filename
        return pd.read_parquet(target_path)

    def write_to_package(self, df: pd.DataFrame, resource: Resource):
        target_filename = resource.name + ".parquet"
        target_path = self.dp.get_path() / target_filename
        logger.info(f"Writing parquet file to package at {target_path}")
        write_parquet(df, target_path)

    ######################################
    # MISC.
    ######################################

    def load_conn(self) -> duckdb.DuckDBPyConnection:
        return load_conn()

    @staticmethod
    def clean_str(s: str) -> str:
        return re.sub(r"[^a-z0-9._-]", "", s.strip().lower())

    def create_resource(self, name: str, schema: Schema) -> Resource:
        """
        Create and return a Resource object with the specified schema
        """
        resource_name = self.clean_str(name)
        logger.info(f"Creating resource '{resource_name}'")
        return Resource(
            name=resource_name,
            path=f"{resource_name}.parquet",
            schema=schema,
        )
