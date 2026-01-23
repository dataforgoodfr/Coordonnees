from .openmaptiles import OpenMapTilesParser
from .sql import SQLParser
from .xyzservices import XYZServicesParser


def get_parser(type_):
    parsers = {
        "xyzservices": XYZServicesParser(),
        "openmaptiles": OpenMapTilesParser(),
        "sql": SQLParser(),
    }
    return parsers[type_]
