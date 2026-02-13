from coordo.layers.base import LayerConfig

from .datapackage import DataPackageParser
from .openmaptiles import OpenMapTilesParser
from .xyzservices import XYZServicesParser


def get_parser(type_) -> LayerConfig:
    parsers = {
        "xyzservices": XYZServicesParser,
        "openmaptiles": OpenMapTilesParser,
        "datapackage": DataPackageParser,
    }
    return parsers[type_]
