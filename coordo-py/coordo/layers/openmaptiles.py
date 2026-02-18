from typing import Any, Literal, Optional

from ..maplibre_style_spec_v8 import Layer, Source
from .base import BaseConfig

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


class OpenMapTilesLayer(BaseConfig):
    type: Literal["openmaptiles"]
    layer: str
    filters: Optional[dict[str, Any]] = None

    def to_maplibre(self, base_path=None):
        layer: Layer = {
            "id": self.id,
            "source": "openmaptiles",
            "source-layer": self.layer,
            "filter": (
                "all",
                *(("==", ("get", key), value) for key, value in self.filters.items()),
            ),
        }
        if self.layer == "boundary":
            layer.update(BOUNDARY_LAYER)
        else:
            layer.update(PLACE_LAYER)
        return {SOURCE_ID: SOURCE}, layer
