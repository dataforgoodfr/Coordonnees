import json
from pathlib import Path

from coordo import to_maplibre
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render


def index(request):
    return render(request, "cartasso/index.html")


config_path = Path("data/config.json")


def sources_view(request):
    sources = [p for p in Path("cartasso/catalog").iterdir() if p.is_dir()]
    return HttpResponse(sources)


def style_json(request):
    config = json.load(config_path.open())
    return JsonResponse(to_maplibre(config))
