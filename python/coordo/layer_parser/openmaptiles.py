from typing import Literal

from coordo.layer_parser.maplibre_style_spec_v8 import (
    Layer,
    Source,
)

from .base import LayerConfig, LayerParser

SOURCE_ID = "openmaptiles"
SOURCE: Source = {
    "type": "vector",
    "url": "https://tiles.openfreemap.org/planet",
}

PLACE_LAYER = {
    "type": "symbol",
    "layout": {
        "icon-allow-overlap": True,
        "icon-image": ["step", ["zoom"], "circle_11_black", 10, ""],
        "icon-optional": False,
        "icon-size": 0.2,
        "text-anchor": "bottom",
        "text-field": [
            "case",
            ["has", "name:nonlatin"],
            [
                "concat",
                ["get", "name:latin"],
                "\n",
                ["get", "name:nonlatin"],
            ],
            ["coalesce", ["get", "name_en"], ["get", "name"]],
        ],
        "text-font": ["Noto Sans Regular"],
        "text-max-width": 8,
        "text-size": [
            "interpolate",
            ["exponential", 1.2],
            ["zoom"],
            7,
            10,
            11,
            12,
        ],
    },
    "paint": {
        "text-color": "#000",
        "text-halo-blur": 1,
        "text-halo-color": "#fff",
        "text-halo-width": 1,
    },
}
BOUNDARY_LAYER = {"type": "line"}


class OpenMapTilesLayerConfig(LayerConfig):
    type: Literal["openmaptiles"]
    layer: str
    filters: dict[str, str]


class OpenMapTilesParser(LayerParser):
    def parse(self, config: OpenMapTilesLayerConfig):
        layer: Layer
        if config["layer"] == "boundary":
            layer = {
                "type": "line",
                "source": "openmaptiles",
                "source-layer": config["layer"],
                "filter": (
                    "all",
                    *(
                        ("==", ("get", key), value)
                        for key, value in config["filters"].items()
                    ),
                ),
            }
        else:
            layer = {
                "type": "line",
                "source": "openmaptiles",
                "source-layer": config["layer"],
                "filter": (
                    "all",
                    *(
                        ("==", ("get", key), value)
                        for key, value in config["filters"].items()
                    ),
                ),
            }
        return {SOURCE_ID: SOURCE}, layer
