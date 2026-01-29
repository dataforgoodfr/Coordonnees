import json
from pathlib import Path

from coordo.layer_parser import to_maplibre
from django.http import JsonResponse
from django.shortcuts import render


def index(request):
    return render(request, "cartasso/index.html")


config_path = Path("data/config.json")


def style_json(request):
    config = json.load(config_path.open())
    return JsonResponse(to_maplibre(config))
