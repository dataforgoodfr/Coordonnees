# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import shutil
from pathlib import Path
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
        query= csv_query(self.path, sep=self.sep, decimal_sep=self.decimal_sep) if extension == ".csv" else f"""
            SELECT * FROM {prepare_path(self.path)}
        """

        conn, _ = self.dp.prepare_db()
        rel = conn.sql(query)
        schema = Schema()

        for name, type in zip(rel.columns, rel.types):
            schema.add_field(Field(name=name, **to_dp_type(type)))

        conn.close()

        # creating resurce for file
        resource = Resource(
            name=self.path.stem,
            path=self.path.name,
            schema=schema,
        )
        self.resources = [resource]

    def transform(self):
        pass

    def load(self):
        shutil.copy(self.path, self.dp._basepath / self.path.name)


def csv_query(path: Path, sep: Separator = Separator.COMMA, decimal_sep: Separator = Separator.DOT):
    return f"""
        SELECT * 
        FROM read_csv({prepare_path(path)}, sep='{sep.value}', decimal_separator='{decimal_sep.value}', auto_detect=true)
    """