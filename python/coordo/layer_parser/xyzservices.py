import xyzservices.providers as providers

from coordo.layer_parser.maplibre_style_spec_v8 import RasterLayer, RasterSource, Source

from .base import LayerParser


class XYZServicesParser(LayerParser):
    def parse(self, config):
        provider = providers
        for part in config["provider"].split("."):
            provider = getattr(provider, part)
        source_name = str(provider.name)
        source: RasterSource = {
            "type": "raster",
            "tiles": [provider.build_url()],
        }
        source_dict = {source_name: source}
        layer: RasterLayer = {
            "type": "raster",
            "source": source_name,
        }
        return source_dict, layer
