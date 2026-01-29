import json
from pathlib import Path

from coordo.layer_parser import to_maplibre

config = json.load(Path("../data/config.json").open())
print(to_maplibre(config))
