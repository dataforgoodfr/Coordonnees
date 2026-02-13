import xyzservices.providers as providers

from .base import LayerConfig
from .maplibre_style_spec_v8 import RasterLayer, RasterSource


class XYZServicesParser(LayerConfig):
    provider: str

    def to_maplibre(self):
        provider = providers
        for part in self.provider.split("."):
            provider = getattr(provider, part)
        source_name = str(provider.name)
        source: RasterSource = {
            "type": "raster",
            "tiles": [provider.build_url()],
        }
        source_dict = {source_name: source}
        layer: RasterLayer = {
            "id": self.id,
            "type": "raster",
            "source": source_name,
        }
        return source_dict, layer
