# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import json
import logging
import os
import tempfile
import time
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import ClassVar

import geopandas as gpd
import pandas as pd
import pyarrow.parquet as pq
from pandas import DataFrame

from ..datapackage import DataPackage, Resource

logger = logging.getLogger(__name__)


class UpdateMethod(str, Enum):
    APPEND = "append"
    REPLACE = "replace"

def write_parquet(df: DataFrame, path: Path | str):
    target_path = Path(path)
    start = time.perf_counter()

    logger.info(
        f"[PERF] write_parquet START: path={target_path} rows={len(df)}"
    )

    if not target_path.parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {target_path.parent}")

    fd, temp_path = tempfile.mkstemp(
        prefix=f".{target_path.stem}.",
        suffix=".parquet",
        dir=target_path.parent
    )
    os.close(fd)
    temp_path = Path(temp_path)

    try:
        write_start = time.perf_counter()

        if isinstance(df, gpd.GeoDataFrame):
            df.to_parquet(
                temp_path,
                schema_version="1.1.0",
                index=False,
                write_covering_bbox=True,
                geometry_encoding="WKB",
            )
        elif isinstance(df, DataFrame):
            df.to_parquet(temp_path, index=False)
        else:
            raise TypeError(f"Unknown dataframe type: {type(df)}")

        logger.info(
            f"[PERF] parquet serialization: path={target_path} "
            f"duration={time.perf_counter() - write_start:.4f}s"
        )

        check_start = time.perf_counter()
        pq.read_metadata(temp_path)
        logger.info(
            f"[PERF] parquet metadata check: path={target_path} "
            f"duration={time.perf_counter() - check_start:.4f}s"
        )

        os.replace(temp_path, target_path)

        logger.info(
            f"[PERF] write_parquet END: path={target_path} "
            f"size={target_path.stat().st_size} bytes "
            f"total={time.perf_counter() - start:.4f}s"
        )
    finally:
        temp_path.unlink(missing_ok=True)


def write_parquet__0(df: DataFrame, path: Path | str):
    target_path = Path(path)

    if not target_path.parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {target_path.parent}")

    # Create a temporary file where to write data
    fd, temp_path = tempfile.mkstemp(
        prefix=f".{target_path.stem}.",
        suffix=".parquet",
        dir=target_path.parent
    )
    os.close(fd)
    temp_path = Path(temp_path)

    try:
        if isinstance(df, gpd.GeoDataFrame):
            df.to_parquet(
                temp_path,
                schema_version="1.1.0",
                index=False,
                write_covering_bbox=True,
                geometry_encoding="WKB",  # We use this because duckdb can't open geoarrow as geometries
            )
        elif isinstance(df, DataFrame):
            df.to_parquet(temp_path, index=False)
        else:
            raise TypeError(f"Unknown dataframe type: {type(df)}")

        pq.read_metadata(temp_path)  # Check if the parquet file is readable
        os.replace(temp_path, target_path)  # Move the temp file to the target path
    finally:
        temp_path.unlink(missing_ok=True)  # Clean up the temporary file if it still exists


class Loader(ABC):
    _ACCEPTS_TARGET_RESOURCES: ClassVar[bool] = False

    def __init__(self, package: Path | str):
        self.dp = DataPackage.from_path(package)
        self.resources: list[Resource] = []
        self.dataframes: dict[str, DataFrame | gpd.GeoDataFrame] = {}

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

    def add(self) -> dict:
        """
        Extract the corresponding resources to add, transform, and load them into the package.
        """
        try:
            self.parse_input()
            for resource in self.resources:
                self.dp.attach_resource(resource)
            self.transform()
            self.load()
            self.save()
            return self._success_result("add")
        except Exception as error:  # noqa: BLE001 - operation API returns failures as data
            return self._failure_result("add", error)

    def remove(self) -> dict:
        """
        Extract the correct resources to remove, then remove them from the package.
        """
        try:
            self.parse_input()
            for resource in self.resources:
                self.dp.remove_resource(resource.name)
            self.save()
            return self._success_result("remove")
        except Exception as error:  # noqa: BLE001 - operation API returns failures as data
            return self._failure_result("remove", error)

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

    def append(self, resource_name: str | None = None) -> dict:
        """
        High level method that abstracts appending data to resources.
        """
        try:
            duplicates = self.update(
                method=UpdateMethod.APPEND, resource_name=resource_name
            )
            return self._success_result("append", duplicates=duplicates)
        except Exception as error:  # noqa: BLE001 - operation API returns failures as data
            return self._failure_result("append", error)

    def replace(self, resource_name: str | None = None) -> dict:
        """
        High level method that abstracts replacing data from resources.
        """
        try:
            self.update(method=UpdateMethod.REPLACE, resource_name=resource_name)
            return self._success_result("replace")
        except Exception as error:  # noqa: BLE001 - operation API returns failures as data
            return self._failure_result("replace", error)

    @staticmethod
    def _success_result(operation: str, **extra) -> dict:
        return {
            "success": True,
            "message": f"The {operation} operation has ended successfully",
            **extra,
        }

    @staticmethod
    def _failure_result(operation: str, error: Exception) -> dict:
        logger.exception("The %s operation failed", operation)
        return {
            "success": False,
            "message": f"The {operation} operation has failed",
            "error": str(error),
        }

    def update(self, method: UpdateMethod, resource_name: str | None = None) -> dict:
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
                return self.append_data(resource_name)
            case UpdateMethod.REPLACE:
                self.replace_data(resource_name)
                return {}
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

    def append_datafame_to_resource(
        self, df: DataFrame, resource: Resource
    ) -> list[dict]:
        logger.info(f"Appending data to resource '{resource.name}'")
        current_df = self.dp.read_resource(resource.name)
        # concatenating current and new data
        new_df = pd.concat([current_df, df], ignore_index=True)
        deduplicated_df, duplicates = self.drop_duplicates(new_df, resource)
        # saving concatenated & deduplicated data back to the current resource's path
        self.write_to_package(deduplicated_df, resource)
        return self._dataframe_to_records(duplicates)

    def replace_resource_data_by_dataframe(self, df: DataFrame, resource: Resource):
        logger.info(f"Replacing data in resource '{resource.name}'")
        # saving concatenated data back to the current resource's path
        self.write_to_package(df, resource)

    def drop_duplicates(self, df: DataFrame, resource: Resource):
        """
        Remove duplicate rows in new DataFrame.

        If the resource defines a primary key, use it to identify duplicate
        rows. Otherwise compare all columns.
        Log a warning if duplicates are found.
        """
        primary_key = resource.schema.primaryKey
        if primary_key:
            duplicate_mask = df.duplicated(subset=primary_key)
        else:
            duplicate_mask = df.apply(
                lambda row: tuple(self._make_hashable(value) for value in row),
                axis=1,
            ).duplicated()
        duplicates = df.loc[duplicate_mask]
        if len(duplicates) > 0:
            logger.warning(f"Found {len(duplicates)} duplicate(s) when appending data")
        return df.loc[~duplicate_mask], duplicates

    @staticmethod
    def _dataframe_to_records(df: DataFrame) -> list[dict]:
        def sanitize(value):
            if isinstance(value, str):
                return value.encode("utf-8", errors="replace").decode("utf-8")
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="replace")
            if isinstance(value, dict):
                return {sanitize(key): sanitize(item) for key, item in value.items()}
            if isinstance(value, list):
                return [sanitize(item) for item in value]
            if isinstance(value, tuple):
                return tuple(sanitize(item) for item in value)
            return value

        sanitized_df = pd.DataFrame(df).map(sanitize)
        sanitized_df.columns = [sanitize(column) for column in sanitized_df.columns]
        return json.loads(
            sanitized_df.to_json(
                orient="records", date_format="iso", default_handler=str
            )
        )

    @staticmethod
    def _make_hashable(value):
        """
        Recursively convert mutable values into hashable equivalents.

        This allows rows containing lists, dictionaries, sets, or tuples to
        be compared reliably when a resource has no primary key and duplicate
        detection must use the complete row.
        """
        if isinstance(value, list):
            return tuple(Loader._make_hashable(item) for item in value)
        if isinstance(value, dict):
            return tuple(
                sorted(
                    (key, Loader._make_hashable(item))
                    for key, item in value.items()
                )
            )
        if isinstance(value, set):
            return frozenset(Loader._make_hashable(item) for item in value)
        if isinstance(value, tuple):
            return tuple(Loader._make_hashable(item) for item in value)
        return value

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
    # HANDLE PRIMARY KEYS
    ######################################

    @staticmethod
    def replace_primary_key(
        package: Path | str,
        resource_name: str,
        fields: list[str],
    ):
        dp = DataPackage.from_path(package)
        resource = dp.get_resource(resource_name)
        resource.replace_primary_key(fields)
        dp.save()

    ######################################
    # HANDLE FOREIGN KEYS
    ######################################

    @staticmethod
    def add_foreign_key(
        package: Path | str,
        resource_name: str,
        foreign_resource_name: str,
        pairs: list[str],
    ):
        dp = DataPackage.from_path(package)
        resource = dp.get_resource(resource_name)
        fields = pairs[::2]
        foreign_fields = pairs[1::2]
        resource.add_foreignkey(fields, foreign_fields, foreign_resource_name)
        dp.save()

    @staticmethod
    def remove_foreign_key(
        package: Path | str,
        resource_name: str,
        foreign_resource_name: str,
    ):
        dp = DataPackage.from_path(package)
        resource = dp.get_resource(resource_name)
        resource.remove_foreignkey(foreign_resource_name)
        dp.save()

    ######################################
    # READ / WRITE PARQUET
    ######################################

    def read_parquet(self, resource: Resource) -> DataFrame:
        target_filename = resource.name + ".parquet"
        target_path = self.dp.get_path() / target_filename

        start = time.perf_counter()
        logger.info(f"[PERF] read_parquet START: path={target_path}")

        df = pd.read_parquet(target_path)

        logger.info(
            f"[PERF] read_parquet END: path={target_path} "
            f"rows={len(df)} columns={len(df.columns)} "
            f"total={time.perf_counter() - start:.4f}s"
        )
        return df

    def write_to_package(self, df: DataFrame, resource: Resource):
        target_filename = resource.name + ".parquet"
        target_path = self.dp.get_path() / target_filename
        logger.info(f"Writing parquet file to package at {target_path}")
        write_parquet(df, target_path)
