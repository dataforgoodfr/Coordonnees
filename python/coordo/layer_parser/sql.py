import geopandas as gpd
from geojson import Feature, FeatureCollection, Point
from peewee import fn
from playhouse.db_url import connect
from playhouse.reflection import generate_models
from playhouse.shortcuts import model_to_dict

from .base import LayerParser

AGG_MAP = {
    "count": lambda field: fn.count(field or "id"),
    "centroid": lambda field: fn.centroid(fn.collect(field)),
}


class SQLParser(LayerParser):
    def parse(self, config):
        db = connect("sqlite:///coordo.sqlite")
        tables = generate_models(db)
        table = tables[config["table"]]
        rows = [model_to_dict(ins, backrefs=True) for ins in table.select()]
        print(rows)
        exit()
        df = gpd.GeoDataFrame(rows)
        group_df = df.groupby(config["groupby"])
        group_df.apply(lambda x: print(x))

        for field, formula in config["fields"].items():
            print(formula)
            parts = formula.split(" ")
            op = parts[0]

        exit()

        if geom_key is None:
            raise ValueError("No geometry field found after aggregation")

        data = FeatureCollection(
            [Feature(geometry=Point(obj.pop(geom_key)), properties=obj) for obj in rows]
        )
        source = {
            "type": "geojson",
            "data": data,
        }
        layer = {
            "id": config["id"],
        }
        return source, layer
