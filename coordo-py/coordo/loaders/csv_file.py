# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import ClassVar
import logging

from coordo.loaders import FileLoader, Separator
from ..datapackage.db_helpers import prepare_path

logger = logging.getLogger(__name__)

class CSVFileLoader(FileLoader):
    
    EXTENSIONS: ClassVar[list[str]] = ['.csv', '.tsv', '.tab']
    
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


    def get_sql_query(self, path: Path) -> str:
        """
        Returns the SQL query to extract the schema from the file.
        """
        return f"""
            SELECT * 
            FROM read_csv({prepare_path(path)}, sep='{self.sep.value}', decimal_separator='{self.decimal_sep.value}', auto_detect=true)
        """


    

        