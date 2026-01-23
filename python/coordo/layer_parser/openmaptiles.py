from .base import LayerParser

SOURCE = {
    "type": "vector",
    "url": "https://tiles.openfreemap.org/planet",
}

DEFAULT_STYLES = {
    "place": {
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
    },
    "boundary": {"type": "line"},
}


class OpenMapTilesParser(LayerParser):
    def parse(self, layer):
        layer = {
            "source": "openmaptiles",
            "source-layer": layer["layer"],
            "filter": [
                "all",
                *(
                    ["==", ["get", key], value]
                    for key, value in layer["filters"].items()
                ),
            ],
            **DEFAULT_STYLES[layer["layer"]],
        }
        return SOURCE, layer
