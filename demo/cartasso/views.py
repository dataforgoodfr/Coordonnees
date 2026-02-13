import json
from pathlib import Path

from coordo import ConfigParser
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from geojson import Feature, FeatureCollection

parser = ConfigParser("data/config.json")


def index(request):
    return render(request, "cartasso/index.html")


def sources_view(request):
    sources = [p for p in Path("cartasso/catalog").iterdir() if p.is_dir()]
    return HttpResponse(sources)


def style_json(request):
    return JsonResponse(parser.to_maplibre())


@csrf_exempt
def map_data(request, layer_id):
    filters = None
    if request.method == "POST":
        payload = request.body.decode("utf-8")
        filters = json.loads(payload)
    geojson = parser.get_data(layer_id, filters)
    return JsonResponse(geojson)
