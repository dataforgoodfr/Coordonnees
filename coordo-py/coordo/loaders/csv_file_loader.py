# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import ClassVar
import logging

from coordo.loaders import FileLoader
from ..datapackage.db_helpers import prepare_path

logger = logging.getLogger(__name__)


class CSVFileLoader(FileLoader):
    EXTENSIONS: ClassVar[list[str]] = [".csv", ".tsv", ".tab"]

    def __init__(
        self,
        package: Path,
        path: Path,
        sep: str = ",",
        decimal_sep: str = ".",
    ):
        super().__init__(package, path)
        if len(sep) > 1:
            raise ValueError("Separator must be a single character")
        if len(decimal_sep) > 1:
            raise ValueError("Decimal separator must be a single character")
        self.sep = sep
        self.decimal_sep = decimal_sep

    def get_sql_query(self, path: Path) -> str:
        """
        Returns the SQL query to extract the schema from the file.
        """
        return f"""
            SELECT * 
            FROM read_csv({prepare_path(path)}, sep='{self.sep}', decimal_separator='{self.decimal_sep}', auto_detect=true)
        """
