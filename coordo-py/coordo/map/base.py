from abc import abstractmethod
from pathlib import Path
from typing import Mapping

from pydantic import BaseModel
from pygeofilter.ast import AstType as Filter

from .maplibre_style_spec_v8 import Layer, Source


class BaseConfig(BaseModel):
    id: str

    @classmethod
    def from_dict(cls, dic):
        return cls.model_validate(dic)

    @abstractmethod
    def to_maplibre(
        self, base_path: Path | None = None
    ) -> tuple[Mapping[str, Source], Layer]:
        pass

    def get_data(self, *, base_path: Path, filter: Filter | None = None):
        raise NotImplementedError
