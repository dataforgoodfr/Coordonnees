import json
from pathlib import Path

from coordo.layer_parser import to_maplibre
from django.http import HttpResponse, JsonResponse


def index(request):
    return HttpResponse(b"Hello World")


config = json.load(Path("config.json").open())


def style_json(request):
    return JsonResponse(to_maplibre(config))
