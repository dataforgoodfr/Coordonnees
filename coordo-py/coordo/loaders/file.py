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


    def load(self):
        for resource in self.resources:
            self.write_to_package(self.dataframes[resource.name], resource)
