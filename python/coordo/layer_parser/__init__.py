from coordo.layer_parser.sql import SQLParser

from .maplibre_style_spec_v8 import Layer, Source, Style
from .openmaptiles import OpenMapTilesParser

# from .sql import SQLParser
from .xyzservices import XYZServicesParser


def get_parser(type_):
    parsers = {
        "xyzservices": XYZServicesParser(),
        "openmaptiles": OpenMapTilesParser(),
        "sql": SQLParser(),
    }
    return parsers[type_]


def to_maplibre(config) -> Style:
    sources: dict[str, Source] = {}
    layers: list[Layer] = []
    for i, layer in enumerate(config["layers"]):
        parser = get_parser(layer["type"])
        source, layer = parser.parse(layer)
        sources.update(source)
        layers.append(layer)
    return {
        "version": 8,
        "sources": sources,
        "layers": layers,
        "metadata": {"controls": config["controls"]},
    }
