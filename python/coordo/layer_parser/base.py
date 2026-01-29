from abc import ABC, abstractmethod
from typing import Mapping, TypedDict

from .maplibre_style_spec_v8 import Layer, Source


class LayerConfig(TypedDict):
    id: str


class LayerParser(ABC):
    @abstractmethod
    def parse(self, config) -> tuple[Mapping[str, Source], Layer]:
        pass
