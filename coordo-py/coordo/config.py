import json
from pathlib import Path
from typing import Any

from geojson.feature import FeatureCollection
from pydantic import BaseModel
from pygeofilter.parsers.cql2_json import parse as parse_cql2

from .layers import LayerUnion
from .maplibre_style_spec_v8 import Layer, Source, Style


class MapConfig(BaseModel):
    title: str | None = None
    layers: list[LayerUnion]
    controls: list[Any]

    _base_path: Path | None = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls.model_validate(data)

    @classmethod
    def from_file(cls, config_path: str | Path):
        path = Path(config_path)
        self = cls.from_dict(json.loads(path.read_text()))
        self._base_path = path.parent
        return self

    def _get_layer(self, layer_id: str):
        layer = next((l for l in self.layers if l.id == layer_id), None)
        if layer is None:
            raise ValueError(f"Layer with id {layer_id} not found")
        return layer

    def get_data(self, layer_id: str, json_filters=None) -> FeatureCollection:
        layer = self._get_layer(layer_id)
        filters = parse_cql2(json_filters) if json_filters else None
        return parser.get_data(filters)

    def to_maplibre(self) -> Style:
        map_sources: dict[str, Source] = {}
        map_layers: list[Layer] = []
        for layer in self.layers:
            sources, layer_kwargs = layer.to_maplibre(self._base_path)
            map_sources.update(sources)
            if "popup" in layer:
                layer_kwargs["metadata"].update({"popup": layer["popup"]})
            layer: Layer = {
                "id": id,
                **layer_kwargs,
            }
            map_layers.append(layer)
        metadata = {}
        if self.controls:
            metadata["controls"] = self.controls
        return {
            "version": 8,
            "name": "coordo",
            "sources": map_sources,
            "layers": map_layers,
            "metadata": metadata,
        }
