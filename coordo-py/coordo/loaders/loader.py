# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from abc import ABC, abstractmethod
from typing import ClassVar
from pathlib import Path
from enum import Enum
import pandas as pd
import geopandas as gpd
import logging

from ..datapackage import DataPackage, Resource


logger = logging.getLogger(__name__)


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


def handle_foreign_key(package: Path | str, from_: str, to: str, method_name: str):
    dp = DataPackage.from_path(package)
    resource, field = from_.split(".")
    foreign_resource, foreign_field = to.split(".")
    resource = dp.get_resource(resource)
    kwargs = dict(
        fields=[field],
        foreign_fields=[foreign_field],
        foreign_resource=foreign_resource,
    )
    method = getattr(resource, method_name)
    method(**kwargs)
    dp.save()


class Loader(ABC):
    _ACCEPTS_TARGET_RESOURCES: ClassVar[bool] = False

    def __init__(self, package: Path | str):
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
    def remove_one_resource(package: Path | str, resource_name: str):
        """
        Remove the specified resource from the package.
        """
        dp = DataPackage.from_path(package)
        dp.remove_resource(resource_name)
        dp.save()

    ######################################
    # UPDATE (APPEND / REPLACE)
    ######################################

    def append(self, resource_name: str | None = None):
        """
        High level method that abstracts appending data to resources.
        """
        self.update(method=UpdateMethod.APPEND, resource_name=resource_name)

    def replace(self, resource_name: str | None = None):
        """
        High level method that abstracts replacing data from resources.
        """
        self.update(method=UpdateMethod.REPLACE, resource_name=resource_name)

    def update(self, method: UpdateMethod, resource_name: str | None = None):
        """
        Update the package with the current resources.
        The backbone of the method is common to both appending and replacing data.
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
        """
        Raise an error if the calling object belongs to a class that does not support
        the 'resource_name' argument when updating data.
        """
        if not self._ACCEPTS_TARGET_RESOURCES:
            raise ValueError(
                f"Cannot supply a target resource name with {self.__class__.__name__}"
            )

    @abstractmethod
    def append_data(self, resource_name: str | None = None):
        """
        Lower level method that defines how classes handle appending data to existing resources
        """
        raise NotImplementedError()

    @abstractmethod
    def replace_data(self, resource_name: str | None = None):
        """
        Lower level method that defines how classes handle replacing data from existing resources
        """
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

    @staticmethod
    def delete_data_from_resource(package: Path | str, resource_name: str):
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
    # HANDLE FOREIGN KEYS
    ######################################

    @staticmethod
    def add_foreign_key(package: Path | str, from_: str, to: str):
        handle_foreign_key(package, from_, to, method_name="add_foreignkey")

    @staticmethod
    def remove_foreign_key(package: Path | str, from_: str, to: str):
        handle_foreign_key(package, from_, to, method_name="remove_foreignkey")

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
