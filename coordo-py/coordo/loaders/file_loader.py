# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
import pandas as pd
import shutil

from coordo.loaders import Loader, ResourceAction, Separator
from ..datapackage import Field, Resource, Schema
from ..datapackage.db_helpers import prepare_path, to_dp_type


class FileLoader(Loader):
    def __init__(
        self,
        package: Path,
        path: Path,
        action: ResourceAction,
        sep: Separator = Separator.COMMA,
        decimal_sep: Separator = Separator.DOT
    ):
        super().__init__(package, action)
        self.path = path
        self.sep = sep
        self.decimal_sep = decimal_sep

    def extract(self):
        extension = self.path.suffix.lower()

        if extension == ".xlsx":
            self.readExcelFile()

        else:
            query= csv_query(self.path, sep=self.sep, decimal_sep=self.decimal_sep) if extension == ".csv" else f"""
                SELECT * FROM {prepare_path(self.path)}
            """
            self.resources = [self._create_resource(self.path, query)]

    def transform(self):
        pass

    def load(self):
        shutil.copy(self.path, self.dp._basepath / self.path.name)


    def readExcelFile(self):
        sheets = pd.read_excel(self.path, sheet_name=None)
        for i, (sheet_name, sheet) in enumerate(sheets.items()):
            path = Path(self.dp._basepath, sheet_name + '.parquet')
            sheet['_index'] = sheet.index + 1
            # to_parquet method fails if column names contain dots
            sheet.columns = [col.replace('.', '_') for col in sheet.columns]
            sheet.to_parquet(path, index=False)
            query= f"SELECT * FROM {prepare_path(path)}"

            self.resources.append(self._create_resource(path, query))


    def _create_resource(self, path: Path, query: str) -> Resource:
        schema = Schema()
        conn, _ = self.dp.prepare_db()
        rel = conn.sql(query)

        for name, type in zip(rel.columns, rel.types):
            schema.add_field(Field(name=name, **to_dp_type(type)))

        conn.close()

        # creating resurce for file
        return Resource(
            name=path.stem,
            path=path.name,
            schema=schema,
        )
    
def csv_query(path: Path, sep: Separator = Separator.COMMA, decimal_sep: Separator = Separator.DOT):
    return f"""
        SELECT * 
        FROM read_csv({prepare_path(path)}, sep='{sep.value}', decimal_separator='{decimal_sep.value}', auto_detect=true)
    """