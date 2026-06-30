# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from abc import abstractmethod
import pandas as pd
import shutil
import logging


from coordo.loaders import Loader


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


    @abstractmethod
    def get_sql_query(self, path: Path) -> str:
        """
        Returns the SQL query to extract the schema from the file.
        """
        raise NotImplementedError()
        

    def check_resource_not_exists(self):
        if self.dp.resource_exists(self.path.stem):
            raise ValueError(f"Resource already exists: '{self.path.stem}'")
