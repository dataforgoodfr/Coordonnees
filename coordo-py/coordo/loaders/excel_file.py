# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
import pandas as pd
import logging

from coordo.loaders import FileLoader
from ..datapackage import Schema, Field
from ..datapackage.db_helpers import prepare_path, pandas_type_to_dp_type

logger = logging.getLogger(__name__)

class ExcelFileLoader(FileLoader):

    # see https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_excel.html
    EXTENSIONS = ['.xlsx', '.xls', '.xlsm', '.xlsb', '.odf', '.ods', '.odt'] 
    
    def __init__(
        self,
        package: Path,
        path: Path
    ):
        super().__init__(package, path)


    def get_sql_query(self, path: Path) -> str:
        """
        Returns the SQL query to extract the schema from the file.
        """
        return f"""
            SELECT * FROM {prepare_path(path)}
        """
            

    def parse_input(self):
        """
        Parses the input Excel file and writes each sheet to the raw staging directory as a parquet file.
        The parsing is performed with pandas instead of duckdb because duckdb only support '.xlsx' files
        while pandas supports multiple formats
        """
        sheets = pd.read_excel(self.path, sheet_name=None)
        for i, (sheet_name, sheet) in enumerate(sheets.items()):
            path = self.dp.get_path() / (sheet_name + '.parquet')
            sheet['_index'] = sheet.index + 1
            
            schema = Schema()
            # to_parquet method fails if column names contain dots
            sheet.columns = [col.replace('.', '_') for col in sheet.columns]
            # parse schema from the SQL query result
            for name, type in sheet.dtypes.items():
                schema.add_field(Field(name=name, **pandas_type_to_dp_type(type)))
                
            # creating a new resource
            resource = self.create_resource(path.stem, schema)
            # writing the data parsed from the file to the raw staging directory as a parquet file
            self.write_to_staging(sheet, resource.name)
            self.resources.append(resource)


    def append_data(self, resource_name: str | None = None):
        pass


    def replace_data(self, resource_name: str | None = None):
        pass


    def transform(self, resource_name: str | None = None):
        pass


    def load(self):
        for resource in self.resources:
            df = self.read_from_staging(resource.name)
            self.write_to_package(df, resource)