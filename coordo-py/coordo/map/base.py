# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import Mapping

from pydantic import BaseModel
from pygeofilter.ast import AstType as Filter

from .maplibre_style_spec_v8 import Layer, Source


class BaseLayerModel(BaseModel):
    id: str
    type: str

    @classmethod
    def from_dict(cls, dic):
        return cls.model_validate(dic)

    def to_maplibre(self, base_path: Path) -> tuple[Mapping[str, Source], Layer]:
        raise NotImplementedError

    def get_data(self, *, base_path: Path, filter: Filter | None = None):
        raise NotImplementedError
