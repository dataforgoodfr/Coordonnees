# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import ClassVar
import pandas as pd
import logging

from coordo.loaders import Loader
from ..datapackage import Resource, Schema, Field
from ..datapackage.db_helpers import prepare_path, duckdb_type_to_dp_type


logger = logging.getLogger(__name__)


class FileLoader(Loader):
    _ACCEPTS_TARGET_RESOURCES: ClassVar[bool] = True

    resource: Resource

    def __init__(self, package: Path | str, path: Path | str):
        super().__init__(package)
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

    def get_sql_query(self, path: Path) -> str:
        """
        Returns the SQL query to extract the schema from the file.
        """
        return f"""
            SELECT * FROM {prepare_path(path)}
        """

    def parse_file(self, path: Path) -> tuple[Resource, pd.DataFrame]:
        """
        Parse a file and infer its schema using a SQL query.
        The DuckDB engine can read both parquet and CSV files.
        Create a resource from the schema and the provided path.
        Parses data from the file and writes it to the raw staging directory.
        """
        schema = Schema()
        with self.load_conn() as conn:
            sql_query = self.get_sql_query(path)
            rel = conn.sql(sql_query)

            # parse schema from the SQL query result
            for name, type in zip(rel.columns, rel.types):
                schema.add_field(Field(name=name, **duckdb_type_to_dp_type(type)))

            # creating a new resource
            resource = self.create_resource(path.stem, schema)
            # parsing data from the file
            df = rel.to_df()

        return resource, df

    def parse_input(self):
        self.resource, df = self.parse_file(self.path)
        self.resources = [self.resource]
        # storing parsed dataframe
        self.dataframes[self.resource.name] = df

    def transform(self):
        # TODO: if needed, implement transformation logic here or in child classes
        pass

    def append_data(self, resource_name: str | None = None):
        # if no resource name is provided, use the current resource's name
        resource_name = resource_name or self.resource.name
        resource = self.dp.get_resource(resource_name)
        df = self.dataframes[self.resource.name]
        self.append_datafame_to_resource(df, resource)

    def replace_data(self, resource_name: str | None = None):
        # if no resource name is provided, use the current resource's name
        resource_name = resource_name or self.resource.name
        resource = self.dp.get_resource(resource_name)
        df = self.dataframes[self.resource.name]
        self.replace_resource_data_by_dataframe(df, resource)
