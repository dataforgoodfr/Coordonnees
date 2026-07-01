# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
import pandas as pd
import logging

from coordo.loaders import Loader
from ..datapackage import Resource, Schema, Field
from ..datapackage.db_helpers import prepare_path, duckdb_type_to_dp_type


logger = logging.getLogger(__name__)


class FileLoader(Loader):
    def __init__(
        self,
        package: Path,
        path: Path
    ):
        super().__init__(package)
        self.path = path
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
        logger.info(f"Appending data to resource '{resource_name}'")
        existing_resource = self.dp.get_resource(resource_name)
        current_df = self.dp.read_resource(existing_resource.name)
        # concatenating current and new data
        df = pd.concat([
            current_df, 
            self.dataframes[self.resource.name]
        ], ignore_index=True)
        # saving concatenated data back to the current resource's path
        self.write_to_package(df, existing_resource)


    def replace_data(self, resource_name: str | None = None):
        # if no resource name is provided, use the current resource's name
        resource_name = resource_name or self.resource.name
        logger.info(f"Replacing data in resource '{resource_name}'")
        existing_resource = self.dp.get_resource(resource_name)
        # saving concatenated data back to the current resource's path
        self.write_to_package(
            self.dataframes[self.resource.name],
            existing_resource
        )


    def load(self):
        for resource in self.resources:
            self.write_to_package(self.dataframes[resource.name], resource)
