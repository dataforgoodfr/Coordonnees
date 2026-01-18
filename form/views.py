import xyzservices.providers as xyz
from django.contrib.gis.db.models import Collect
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from dynamic_models.models import ModelSchema
from geojson import Feature, FeatureCollection, Point

openmaptiles_style_map = {
    "place": {
        "type": "symbol",
        "layout": {
            "icon-allow-overlap": True,
            "icon-image": ["step", ["zoom"], "circle_11_black", 10, ""],
            "icon-optional": False,
            "icon-size": 0.2,
            "text-anchor": "bottom",
            "text-field": [
                "case",
                ["has", "name:nonlatin"],
                [
                    "concat",
                    ["get", "name:latin"],
                    "\n",
                    ["get", "name:nonlatin"],
                ],
                ["coalesce", ["get", "name_en"], ["get", "name"]],
            ],
            "text-font": ["Noto Sans Regular"],
            "text-max-width": 8,
            "text-size": [
                "interpolate",
                ["exponential", 1.2],
                ["zoom"],
                7,
                10,
                11,
                12,
            ],
        },
        "paint": {
            "text-color": "#000",
            "text-halo-blur": 1,
            "text-halo-color": "#fff",
            "text-halo-width": 1,
        },
    },
    "boundary": {"type": "line"},
}


def index(request):
    return render(request, "form/index.html")


config = {
    "layers": [
        {
            "id": "satellite",
            "type": "xyzservices",
            # "provider": "OpenTopoMap",
            "provider": "Esri.WorldImagery",
        },
        {
            "id": "villages",
            "type": "openmaptiles",
            "layer": "place",
            "filters": {"class": "village"},
        },
        {
            "id": "towns",
            "type": "openmaptiles",
            "layer": "place",
            "filters": {"class": "town"},
        },
        {
            "id": "boundaries",
            "type": "openmaptiles",
            "layer": "boundary",
            "filters": {"admin_level": 2},
            "style": {"paint": {"line-color": "hsl(248,7%,66%)"}},
        },
        {
            "id": "placettes",
            "type": "sql",
            "table": "inventaire_ID",
            "transform": [
                {
                    "groupby": ["cod"],
                    "aggregate": [
                        {"op": "count", "as": "count"},
                        {"op": "centroid", "field": "gps", "as": "center"},
                    ],
                }
            ],
            "popup": {
                "trigger": "click",
                "html": "<h1>Placette {{ cod }}</h1>{{ count }} réponses",
            },
        },
    ],
    "controls": [
        {
            "type": "compass",
            "position": "top-left",
        },
        {
            "type": "layer",
            "position": "top-right",
        },
        {
            "type": "scale",
            "position": "bottom-left",
        },
    ],
}


AGG_MAP = {
    "count": lambda field: Count(field or "id"),
    "centroid": lambda field: Centroid(Collect(field)),
}


def source_to_geojson(source):
    models = [
        schema.as_model()
        for schema in ModelSchema.objects.filter(name__startswith=source["table"])
    ]
    model = models[0]

    transform = source["transform"][0]
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

    return FeatureCollection(
        [Feature(geometry=Point(obj.pop(geom_key)), properties=obj) for obj in rows]
    )


def style(request):
    sources = {}
    layers = []
    for i, layer in enumerate(config["layers"]):
        dic = {
            "id": layer["id"],
        }
        match layer["type"]:
            case "xyzservices":
                provider = xyz
                for part in layer["provider"].split("."):
                    provider = getattr(provider, part)
                sources[provider.name] = {
                    "type": "raster",
                    "tiles": [provider.build_url()],
                }
                dic.update(
                    {
                        "type": "raster",
                        "source": provider.name,
                    },
                )
            case "openmaptiles":
                if "openmaptiles" not in sources:
                    sources["openmaptiles"] = {
                        "type": "vector",
                        "url": "https://tiles.openfreemap.org/planet",
                    }
                dic.update(
                    {
                        "source": "openmaptiles",
                        "source-layer": layer["layer"],
                        "filter": [
                            "all",
                            *(
                                ["==", ["get", key], value]
                                for key, value in layer["filters"].items()
                            ),
                        ],
                        **openmaptiles_style_map[layer["layer"]],
                    }
                )
            case "sql":
                sources[layer["table"]] = {
                    "type": "geojson",
                    "data": source_to_geojson(layer),
                }
                dic.update(
                    {
                        "type": "circle",
                        "source": layer["table"],
                    }
                )
        if "popup" in layer:
            dic["metadata"] = {"popup": layer["popup"]}
        if "style" in layer:
            dic.update(layer["style"])
        layers.append(dic)
    return JsonResponse(
        {
            "version": 8,
            "sources": sources,
            "layers": layers,
            "metadata": {"controls": config["controls"]},
        }
    )
