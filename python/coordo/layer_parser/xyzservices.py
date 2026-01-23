import xyzservices.providers as providers

from .base import LayerParser


class XYZServicesParser(LayerParser):
    def parse(self, layer):
        provider = providers
        for part in layer["provider"].split("."):
            provider = getattr(provider, part)
        source = {
            provider.name: {
                "type": "raster",
                "tiles": [provider.build_url()],
            }
        }
        layer = {
            "id": layer["id"],
            "type": "raster",
            "source": provider.name,
        }
        return source, layer
