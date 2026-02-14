from geojson import Feature, FeatureCollection
from pygeofilter.ast import And, Condition
from pygeofilter.parsers.cql2_text import parse

from coordo.datapackage import DataPackage
from coordo.layers.maplibre_style_spec_v8 import Layer, Source

from .base import LayerConfig


class DataPackageParser(LayerConfig):
    path: str
    resource: str
    filter: str | None = None
    groupby: list[str] | None = None
    aggregate: dict[str, str] | None = None

    def to_maplibre(self):
        id: str = self.id
        source: Source = {"type": "geojson", "data": ""}
        resource = self._package.get_resource(self.resource)
        layer: Layer = {
            "type": "circle",
            "id": id,
            "source": id,
            "metadata": {"schema": resource.schema.model_dump(exclude_none=True)},
        }
        return {id: source}, layer

    @property
    def _package(self):
        return DataPackage.from_path(self.path)

    def get_data(self, filter=None) -> FeatureCollection:
        package = self._package
        final_filter = None
        if self.filter:
            final_filter = parse(self.filter)
        if filter:
            if final_filter:
                final_filter = And(final_filter, filter)
            else:
                final_filter = filter
        it = package.read_data(
            self.resource, final_filter, self.groupby, self.aggregate
        )
        return FeatureCollection(
            features=[
                Feature(
                    geometry=row["geometry"],
                    properties={k: v for k, v in row.items() if k != "geometry"},
                )
                for row in it
            ]
        )
