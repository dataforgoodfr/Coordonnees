# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import ClassVar

import pandas as pd
import logging

from coordo.loaders import FileLoader
from ..datapackage import Schema, Field, Resource
from ..datapackage.db_helpers import pandas_type_to_dp_type

logger = logging.getLogger(__name__)

class ExcelFileLoader(FileLoader):

    # see https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_excel.html
    EXTENSIONS: ClassVar[list[str]] = ['.xlsx', '.xls', '.xlsm', '.xlsb', '.odf', '.ods', '.odt'] 
    
    def __init__(
        self,
        package: Path,
        path: Path
    ):
        super().__init__(package, path)
            

    def parse_input(self):
        """
        Parses the input Excel file and creates a new resource for each sheet.
        """
        table_name_to_df_dict: dict[str, pd.DataFrame] = pd.read_excel(self.path, sheet_name=None)
        for i, (sheet_name, sheet_df) in enumerate(table_name_to_df_dict.items()):
            path = self.dp.get_path() / (sheet_name + '.parquet')
            sheet_df['_index'] = sheet_df.index + 1
            
            schema = Schema()
            # to_parquet method fails if column names contain dots
            sheet_df.columns = [col.replace('.', '_') for col in sheet_df.columns]
            # parse schema from the SQL query result
            for name, dtype in sheet_df.dtypes.items():
                schema.add_field(Field(name=name, **pandas_type_to_dp_type(dtype)))
                
            # creating a new resource
            resource = self.create_resource(path.stem, schema)
            # writing the data parsed from the file to the raw staging directory as a parquet file
            self.dataframes[resource.name] = sheet_df
            self.resources.append(resource)


    def get_resources_to_update(self, resource_name: str | None = None) -> list[Resource]:
        # if a target resource was provided
        # check that only one resource is present in the Excel file
        if resource_name is not None:
            if len(self.resources) > 1:
                raise ValueError(
                    "Updating a specific resource is not supported for Excel files comprising multiple sheets."
                )
            return [self.dp.get_resource(resource_name)]
        else:
            return self.resources


    def append_data(self, resource_name: str | None = None):
        target_resources = self.get_resources_to_update(resource_name)
        for resource in target_resources:
            logger.info(f"Appending data to resource '{resource.name}'") 
            current_df = self.dp.read_resource(resource.name)
            # concatenating current and new data
            df = pd.concat([
                current_df, 
                self.dataframes[resource.name]
            ], ignore_index=True)
            # saving concatenated data back to the current resource's path
            self.write_to_package(df, resource)


    def replace_data(self, resource_name: str | None = None):
        target_resources = self.get_resources_to_update(resource_name)
        for resource in target_resources:
            logger.info(f"Replacing data in resource '{resource.name}'")
            existing_resource = self.dp.get_resource(resource.name)
            # saving concatenated data back to the current resource's path
            self.write_to_package(
                self.dataframes[resource.name],
                existing_resource
            )