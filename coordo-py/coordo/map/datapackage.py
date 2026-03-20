from typing import Literal

from geojson import FeatureCollection
from geopandas.geodataframe import GeoDataFrame
from pydantic import BaseModel
from pygeofilter.ast import And
from pygeofilter.parsers.cql2_text import parse

from coordo.datapackage import DataPackage

from ..helpers import safe
from .base import BaseLayerModel
from .maplibre_style_spec_v8 import GeoJSONSource, Layer


class Popup(BaseModel):
    trigger: str
    html: str | None = None


class DataPackageLayer(BaseLayerModel):
    type: Literal["datapackage"]
    path: str
    resource: str
    filter: str | None = None
    groupby: list[str] | None = None
    columns: dict[str, str] | None = None
    popup: Popup | None = None

    def to_maplibre(self, base_path):
        package = DataPackage.from_path(base_path / self.path)
        resource = package.get_resource(name=self.resource)
        data = self.get_data(base_path=base_path)

        # We check the type of the first non-null geometry, it doesn't support yet mixed geometries
        geom_type = (
            next(f["geometry"] for f in data["features"] if f["geometry"])["type"]
            if data["features"]
            else "Point"
        )
        if "Polygon" in geom_type:
            layer_type = "fill"
        elif "LineString" in geom_type:
            layer_type = "line"
        else:
            layer_type = "circle"

        source = GeoJSONSource(type="geojson", data=data)
        metadata = {
            "schema": safe(resource, "schema").model_dump(
                exclude_none=True, warnings="none"
            ),
        }
        if self.popup:
            metadata.update(popup=self.popup.model_dump())
        layer: Layer = {
            "id": self.id,
            "type": layer_type,
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
        df = package.read_resource(
            self.resource,
            self.columns,
            final_filter,
            self.groupby,
        )
        assert isinstance(df, GeoDataFrame), "No geometries in the layer output."
        return df.to_geo_dict(show_bbox=True)  # type: ignore
