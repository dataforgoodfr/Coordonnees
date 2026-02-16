import json
from pathlib import Path
from urllib.parse import urljoin

from geojson.feature import FeatureCollection
from pygeofilter.parsers.cql2_json import parse as parse_cql2

from .layers import get_parser
from .layers.maplibre_style_spec_v8 import Layer, Source, Style


class ConfigParser:
    def __init__(self, config_path, base_url: str = ""):
        path = Path(config_path)
        self.base_path = path.parent
        self.base_url = base_url
        self.config = json.load(path.open())
        for layer in self.config["layers"].values():
            if "path" in layer:
                layer_path = Path(layer["path"])
                if not layer_path.is_absolute():
                    layer["path"] = str(self.base_path / layer_path)

    def _get_layer(self, layer_id: str):
        layer = self.config["layers"][layer_id]
        return {"id": layer_id, **layer}

    def get_data(self, layer_id: str, json_filters=None) -> FeatureCollection:
        layer = self._get_layer(layer_id)
        parser = get_parser(layer["type"]).from_dict(layer)
        filters = parse_cql2(json_filters) if json_filters else None
        return parser.get_data(filters)

    def to_maplibre(self) -> Style:
        map_sources: dict[str, Source] = {}
        map_layers: list[Layer] = []
        for id, layer in self.config["layers"].items():
            parser = get_parser(layer["type"]).from_dict({"id": id, **layer})
            sources, layer_kwargs = parser.to_maplibre()
            for source in sources.values():
                if "data" in source:
                    source["data"] = "./" + urljoin(self.base_url, id)
            map_sources.update(sources)
            if "popup" in layer:
                layer_kwargs["metadata"].update({"popup": layer["popup"]})
            layer: Layer = {
                "id": id,
                **layer_kwargs,
            }
            map_layers.append(layer)
        return {
            "version": 8,
            "sources": map_sources,
            "layers": map_layers,
            "metadata": {"controls": self.config["controls"]},
        }
