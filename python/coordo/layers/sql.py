from .base import LayerParser
from .query import apply_queries


class SQLParser(LayerParser):
    def parse(self, config):
        gdf = config["source"].get_data()
        if "filters" in config:
            gdf = gdf.query("")
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
