# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import json
from pathlib import Path
from typing import Annotated, Any

from geojson.feature import FeatureCollection
from pydantic import BaseModel, Discriminator
from pygeofilter.parsers.cql2_json import parse as parse_cql2

from .datapackage import DataPackageLayer
from .maplibre_style_spec_v8 import Layer, Source, Style
from .openmaptiles import OpenMapTilesLayer
from .xyzservices import XYZServicesLayer

LayerModel = Annotated[
    DataPackageLayer | OpenMapTilesLayer | XYZServicesLayer, Discriminator("type")
]


class Map(BaseModel):
    title: str | None = None
    layers: list[LayerModel]
    controls: list[Any]

    _base_path: Path | None = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls.model_validate(data)

    def handle_request(self, method: str, path: str, filters: dict | str | bytes):
        if isinstance(filters, (str, bytes)):
            filters = json.loads(filters) if filters else {}
        if method.lower() == "get":
            return self.get_maplibre_style()
        elif method.lower() == "post":
            return self.get_layer_data(path, filters)
        else:
            raise ValueError(f"Method {method.lower()} not supported.")

    @classmethod
    def from_file(cls, config_path: str | Path):
        path = Path(config_path)
        self = cls.from_dict(json.loads(path.read_text()))
        self._base_path = path.parent
        return self

    def _get_layer(self, layer_id: str):
        layer = next((la for la in self.layers if la.id == layer_id), None)
        if layer is None:
            raise ValueError(f"Layer with id {layer_id} not found")
        return layer

    def get_layer_data(
        self, layer_id: str, json_filters: dict | None = None
    ) -> FeatureCollection:
        layer = self._get_layer(layer_id)
        filters = parse_cql2(json_filters) if json_filters else None
        return layer.get_data(base_path=self._base_path, filter=filters)

    def get_maplibre_style(self) -> Style:
        map_sources: dict[str, Source] = {}
        map_layers: list[Layer] = []
        for layer in self.layers:
            sources, layer = layer.to_maplibre(self._base_path)
            map_sources.update(sources)
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
