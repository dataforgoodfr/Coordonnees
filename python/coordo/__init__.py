from coordo.layer_parser import get_parser


def to_maplibre(config):
    sources = []
    layers = []
    for i, layer in enumerate(config["layers"]):
        parser = get_parser(layer["type"])
        source, layer = parser.parse(layer)
        if source not in sources:
            sources.append(source)
        layers.append(layer)
    return {
        "version": 8,
        "sources": sources,
        "layers": layers,
        "metadata": {"controls": config["controls"]},
    }
