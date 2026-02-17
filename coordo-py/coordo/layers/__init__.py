from pydantic import TypeAdapter

from .datapackage import DataPackageLayer
from .openmaptiles import OpenMapTilesLayer
from .xyzservices import XYZServicesLayer

LayerUnion = DataPackageLayer | OpenMapTilesLayer | XYZServicesLayer

adapter = TypeAdapter(LayerUnion)


def LayerConfig(**kwargs):
    return adapter.validate_python(kwargs)
