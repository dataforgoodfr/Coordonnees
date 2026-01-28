import pandas as pd
from geojson import Feature, FeatureCollection, Point

from coordo.sources.kobotoolbox import KoboToolboxSource

from .base import LayerParser

FUNC_MAP = {
    "avg": lambda x: x.mean(),
    "unique": lambda x: x.unique(),
    "centroid": lambda x: x.centroid,
    "count": lambda x: len(x),
}


class SQLParser(LayerParser):
    def parse(self, config):
        gdf = KoboToolboxSource(
            "../data/20250213_Inventaire_ID_QuestionnaireK.xlsx",
            "sqlite:///coordo.sqlite",
        ).get_data()
        group_df = gdf.groupby(config["groupby"])

        for field, formula in config["fields"].items():
            print(formula)
            funcs = []
            col: str | None
            where: str | None = None
            part_it = iter(formula.split(" "))
            for part in part_it:
                if part in FUNC_MAP:
                    funcs.append(FUNC_MAP[part])
                elif part == "where":
                    where = list(part_it)
                else:
                    col = part

            print(where)

            explode: str | None = None
            if "." in col:
                explode, col = col.split(".")

            def apply(df):
                if explode:
                    df = pd.json_normalize(df[explode].explode())
                if where:
                    df = df.query(where)
                df = df[col]
                for func in reversed(funcs):
                    df = func(df)
                return df

            print(group_df.apply(apply))

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
