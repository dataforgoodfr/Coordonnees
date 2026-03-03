from typing import Literal

import numpy as np
from geojson import FeatureCollection
from geopandas.geodataframe import GeoDataFrame
from pydantic import BaseModel
from pygeofilter.ast import And
from pygeofilter.parsers.cql2_text import parse

from coordo.datapackage import DataPackage

from ..helpers import safe
from .base import BaseConfig
from .maplibre_style_spec_v8 import GeoJSONSource, Layer


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

    def to_maplibre(self, base_path):
        package = DataPackage.from_path(base_path / self.path)
        resource = package.get_resource(name=self.resource)
        source = GeoJSONSource(type="geojson", data=self.get_data(base_path=base_path))
        metadata = {
            "schema": safe(resource, "schema").model_dump(
                exclude_none=True, warnings="none"
            ),
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
        df = package.read_resource(
            self.resource, final_filter, self.groupby, self.aggregate
        )
        assert isinstance(df, GeoDataFrame), "No geometries in the layer output."

        # We convert numpy arrays to python lists so the output
        # can be dumped to json
        array_cols = df.select_dtypes(include=np.ndarray, exclude="str").columns
        if not array_cols.empty:
            df[array_cols] = df[array_cols].map(np.ndarray.tolist)

        return df.to_geo_dict()
