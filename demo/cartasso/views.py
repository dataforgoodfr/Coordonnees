import json
from pathlib import Path

from coordo.layer_parser import to_maplibre
from django.http import JsonResponse
from django.shortcuts import render


def index(request):
    return render(request, "cartasso/index.html")


config = json.load(Path("data/config.json").open())


def style_json(request):
    return JsonResponse(to_maplibre(config))
