from geojson import Feature, FeatureCollection

from coordo.datapackage import DataPackage
from coordo.layers.maplibre_style_spec_v8 import Layer, Source

from .base import LayerConfig
from .query import apply_queries


class DataPackageParser(LayerConfig):
    path: str
    resource: str

    def to_maplibre(self):
        id: str = self.id
        source: Source = {"type": "geojson", "data": ""}
        layer: Layer = {
            "type": "circle",
            "id": id,
            "source": id,
            "metadata": {},
        }
        return {id: source}, layer

    def _get_package(self, path):
        return DataPackage.from_path(path)

    def get_data(self, filters=None) -> FeatureCollection:
        package = self._get_package(self.path)
        resource = next(
            resource for resource in package.resources if resource.name == self.resource
        )
        # It takes the first geojson column but we should raise if multiple
        # or ask for a specific one
        geom_col = next(
            field.name for field in resource.schema.fields if field.type == "geojson"
        )
        it = package.read_data(self.resource, filters)
        return FeatureCollection(
            features=[
                Feature(
                    geometry=row[geom_col],
                    properties={k: v for k, v in row.items() if k != geom_col},
                )
                for row in it
            ]
        )
