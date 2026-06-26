# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from coordo.loaders import FileLoader, Separator
from ..datapackage.db_helpers import prepare_path


class CSVFileLoader(FileLoader):
    EXTENSIONS = ['.csv', '.tsv', '.tab']
    
    def __init__(
        self,
        package: Path,
        path: Path,
        sep: Separator = Separator.COMMA,
        decimal_sep: Separator = Separator.DOT
    ):
        super().__init__(package, path)
        self.sep = sep
        self.decimal_sep = decimal_sep

    def extract_and_get_resources(self):
        extension = self.path.suffix.lower()
        query = (
            self.csv_query() if extension == ".csv"
            else f"""
            SELECT * FROM {prepare_path(self.path)}
        """
        )
        self.resources = [self.get_resource(self.path, query)]
    
    def csv_query(self):
        return f"""
            SELECT * 
            FROM read_csv({prepare_path(self.path)}, sep='{self.sep.value}', decimal_separator='{self.decimal_sep.value}', auto_detect=true)
        """