from abc import abstractmethod
from typing import Mapping, Optional

from pydantic import BaseModel
from pygeofilter.ast import AstType

from .maplibre_style_spec_v8 import Layer, Source


class LayerConfig(BaseModel):
    id: str

    @classmethod
    def from_dict(cls, dic):
        return cls.model_validate(dic)

    @abstractmethod
    def to_maplibre(self) -> tuple[Mapping[str, Source], Layer]:
        pass

    def get_data(self, filters: Optional[AstType] = None):
        raise NotImplementedError
