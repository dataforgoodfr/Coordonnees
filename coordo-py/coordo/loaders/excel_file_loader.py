# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
import pandas as pd
import shutil

from coordo.loaders import FileLoader, ResourceAction
from ..datapackage.db_helpers import prepare_path


class ExcelFileLoader(FileLoader):
    def __init__(
        self,
        package: Path,
        path: Path,
        action: ResourceAction
    ):
        super().__init__(package, path, action)

    def extract_and_get_resources(self):
        sheets = pd.read_excel(self.path, sheet_name=None)
        for i, (sheet_name, sheet) in enumerate(sheets.items()):
            path = Path(self.dp._basepath, sheet_name + '.parquet')
            sheet['_index'] = sheet.index + 1
            # to_parquet method fails if column names contain dots
            sheet.columns = [col.replace('.', '_') for col in sheet.columns]
            sheet.to_parquet(path, index=False)
            query= f"SELECT * FROM {prepare_path(path)}"

            resource = self.get_resource(path, query)
            self.resources.append(resource)
 