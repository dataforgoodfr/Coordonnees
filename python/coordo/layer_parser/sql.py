from geojson import Feature, FeatureCollection, Point

from .base import LayerParser

AGG_MAP = {
    "count": lambda field: Count(field or "id"),
    "centroid": lambda field: Centroid(Collect(field)),
}


class SQLParser(LayerParser):
    def parse(self, config):
        models = [
            schema.as_model()
            for schema in ModelSchema.objects.filter(name__startswith=config["table"])
        ]
        model = models[0]

        transform = config["transform"][0]
        annotations = {}
        for agg in transform["aggregate"]:
            op = agg["op"]
            as_ = agg["as"]
            field = agg.get("field")
            if op not in AGG_MAP:
                raise ValueError(f"Unsupported aggregate op: {op}")
            annotations[as_] = AGG_MAP[op](field)

        rows = model.objects.values(*transform["groupby"]).annotate(**annotations)

        geom_key = None
        for key, value in rows[0].items():
            if isinstance(value, GEOSGeometry):
                geom_key = key
                break

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
