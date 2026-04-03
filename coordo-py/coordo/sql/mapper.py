# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from collections import UserDict
from functools import cached_property

from sqlalchemy import Column, MetaData


class FieldDict(UserDict):
    def __setitem__(self, key: str, item: "Column | FieldMapper"):
        if key in self.data:
            raise KeyError(f"Field {key} is already defined.")
        super().__setitem__(key, item)


class FieldMapper:
    def __init__(self, table_name: str, metadata: MetaData, is_reverse=False):
        self.is_reverse = is_reverse
        self.table = metadata.tables[table_name]
        self.metadata = metadata

    def __getitem__(self, key):
        return self.field_map[key]

    @cached_property
    def field_map(self):
        field_map = FieldDict()

        for col in self.table.columns:
            field_map[col.name] = col

        for fk in self.table.foreign_keys:
            tbl = fk.column.table
            if self.table == tbl:
                print("Self-referencing foreign keys are not yet supported.")
            else:
                field_map[tbl.name] = FieldMapper(tbl.name, self.metadata)

        for tbl in self.metadata.tables.values():
            for fk in tbl.foreign_keys:
                if fk.column.table == self.table:
                    field_map[tbl.name] = FieldMapper(
                        tbl.name, self.metadata, is_reverse=True
                    )

        return field_map
