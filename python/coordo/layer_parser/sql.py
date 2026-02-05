from coordo.query import apply_queries

from .base import LayerParser

FUNC_MAP = {
    "avg": lambda x: x.mean(),
    "unique": lambda x: x.unique(),
    "centroid": lambda x: x.centroid,
    "count": lambda x: len(x),
}


class SQLParser(LayerParser):
    def parse(self, config):
        gdf = config["source"].get_data()
        group_df = gdf.groupby(config["groupby"])
        final_df = apply_queries(group_df, config["aggregate"])
        source = {
            config["id"]: {
                "type": "geojson",
                "data": final_df.to_geo_dict(),
            }
        }
        layer = {
            "type": "circle",
            "source": config["id"],
        }
        return source, layer
