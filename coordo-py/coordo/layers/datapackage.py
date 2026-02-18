from pathlib import Path
from typing import Literal

from geojson import Feature, FeatureCollection
from pydantic import BaseModel
from pygeofilter.ast import And
from pygeofilter.parsers.cql2_text import parse

from coordo.datapackage import DataPackage

from ..maplibre_style_spec_v8 import GeoJSONSource, Layer
from .base import BaseConfig


class Popup(BaseModel):
    trigger: str
    html: str | None = None


class DataPackageLayer(BaseConfig):
    type: Literal["datapackage"]
    path: str
    resource: str
    filter: str | None = None
    groupby: list[str] | None = None
    aggregate: dict[str, str] | None = None
    popup: Popup | None = None

    def to_maplibre(self, context=None):
        if not context or "base_path" not in context or "base_url" not in context:
            raise ValueError("You must provide a base_url and a base_path.")
        base_path = Path(context["base_path"])
        base_url = Path(context["base_url"])
        package = DataPackage.from_path(base_path / self.path)
        resource = package.get_resource(self.resource)
        source = GeoJSONSource(type="geojson", data=self.get_data(base_path=base_path))
        metadata = {
            "schema": resource.schema.model_dump(exclude_none=True),
            "url": str(base_url / self.id),
        }
        if self.popup:
            metadata.update(popup=self.popup.model_dump())
        layer: Layer = {
            "id": self.id,
            "type": "circle",
            "source": self.id,
            "metadata": metadata,
        }
        return {self.id: source}, layer

    def get_data(self, *, base_path, filter=None) -> FeatureCollection:
        package = DataPackage.from_path(base_path / self.path)
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
