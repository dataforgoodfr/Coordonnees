from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("style.json", views.style_json, name="style.json"),
    path("<str:layer_id>", views.map_data, name="layers"),
    path("sources", views.sources_view, name="sources"),
]
