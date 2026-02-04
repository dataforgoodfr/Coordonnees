from coordo.sources import parse_source

from .maplibre_style_spec_v8 import Layer, Source, Style
from .openmaptiles import OpenMapTilesParser
from .sql import SQLParser
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
    for source in config["sources"]:
        config["sources"][source] = parse_source(config["sources"][source])
    for i, layer in enumerate(config["layers"]):
        parser = get_parser(layer["type"])
        if "source" in layer:
            layer["source"] = config["sources"][layer["source"]]
        source, layer_kwargs = parser.parse(layer)
        sources.update(source)
        if "popup" in layer:
            layer_kwargs["metadata"] = {"popup": layer["popup"]}
        layer = {
            "id": layer["id"],
            **layer_kwargs,
        }
        layers.append(layer)
    return {
        "version": 8,
        "sources": sources,
        "layers": layers,
        "metadata": {"controls": config["controls"]},
    }
