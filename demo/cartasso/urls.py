from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("style.json", views.style_json, name="style.json"),
]
