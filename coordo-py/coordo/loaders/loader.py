# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from abc import ABC, abstractmethod
from tempfile import gettempdir
from pathlib import Path
from enum import Enum
import pandas as pd
import logging
import duckdb
import shutil
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
    DELETE = "delete"


def write_parquet(df: pd.DataFrame, path: Path | str, geo: bool = False):
    if geo:
        df.to_parquet(
            path,
            schema_version="1.1.0",
            index=False,
            write_covering_bbox=True,
            geometry_encoding="WKB",  # We use this because duckdb can't open geoarrow as geometries
        )
    else:
        df.to_parquet(path, index=False)

    
    
class Loader(ABC):

    RAW_STAGING_DIR = "raw"
    TRANSFORMED_STAGING_DIR = "transformed"

    def __init__(self, package: Path):
        self.dp = DataPackage.from_path(package)
        self.resources: list[Resource] = []
        self.dataframes: dict[str, pd.DataFrame] = {}


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


    @abstractmethod
    def load(self):
        """
        Load physically resources into the package.
        """
        raise NotImplementedError()


    def save(self):
        """
        Invoke the package's save method, which updates the datapackage.json file on disk.
        """
        self.dp.save()


    def add(self):
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
        finally:
            self.delete_staging()
        

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


    def update(self, resource_name: str | None, method: UpdateMethod):
        """
        Update the package with the current resources.
        The method is common whether appending or replacing data.
        """
        try:
            self.parse_input()
            for resource in self.resources:
                self.dp.check_schema_is_compatible(resource)
            self.transform()
            match method:
                case UpdateMethod.APPEND:
                    self.append_data(resource_name)
                case UpdateMethod.REPLACE:
                    self.replace_data(resource_name)
                case UpdateMethod.DELETE:
                    self.delete_data(resource_name)
        finally:
            self.delete_staging()
        # NOTE: there is no need to save here
        # as the modifications are done on the data only, not on the schema


    @abstractmethod
    def append_data(self, resource_name: str | None = None):
        raise NotImplementedError()


    @abstractmethod
    def replace_data(self, resource_name: str | None= None):
        raise NotImplementedError()


    def delete_data(self, resource_name: str | None = None):
        resources = self.get_resources_to_update(resource_name)
        for resource in resources:
            df = self.dp.read_resource(resource.name)
            logger.info(f"Deleting data from resource {resource.name}")
            empty_df_with_same_schema = df.head(0).copy()
            self.write_to_package(empty_df_with_same_schema, resource)


    def get_resources_to_update(self, resource_name: str | None = None) -> list[Resource]:
        """
        Get the resources to update.
        If a resource name is provided, return only the existing resource with that name in the datapackage.
        Otherwise, return all created resources.
        TODO: implement delete cascade
        """
        if resource_name is None:
            return self.resources
        return [self.dp.get_resource(resource_name)]


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


    def read_parquet(self, resource: Resource) -> pd.DataFrame:
        target_filename = resource.name + ".parquet"
        target_path = self.dp.get_path() / target_filename
        return pd.read_parquet(target_path) 


    def write_to_package(self, df: pd.DataFrame, resource: Resource, geo: bool = False):
        target_filename = resource.name + ".parquet"
        target_path = self.dp.get_path() / target_filename
        logger.info(f"Writing parquet file to package at {target_path}")
        write_parquet(df, target_path, geo)


    def get_staging_dir(self) -> Path:
        staging_dir = Path(gettempdir()) / self.dp.name
        staging_dir.mkdir(parents=True, exist_ok=True)
        return staging_dir


    def write_to_staging(self, df: pd.DataFrame, resource_name: str, geo: bool = False):
        target_filename = resource_name + ".parquet"
        target_path = self.get_staging_dir() / target_filename
        logger.info(f"Writing {resource_name} parquet to {target_path}")
        write_parquet(df, target_path, geo)


    def read_from_staging(self, resource_name: str) -> pd.DataFrame:
        target_filename = resource_name + ".parquet"
        target_path = self.get_staging_dir() / target_filename
        return pd.read_parquet(target_path)


    def delete_staging(self):
        staging_dir = self.get_staging_dir()
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
