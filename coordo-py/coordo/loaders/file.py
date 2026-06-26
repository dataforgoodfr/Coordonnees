# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
import shutil
import logging


from coordo.loaders import Loader
from ..datapackage import Field, Resource, Schema
from ..datapackage.db_helpers import to_dp_type

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
        

    def get_resource(self, path: Path, query: str) -> Resource:
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

    def load(self):
        resource = self.resources[0]
        target = self.dp._basepath / self.path.name
        logger.info(f"Saving resource '{resource.name}' to {target}")
        shutil.copy(self.path, target)