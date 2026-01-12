from django.urls import path

from form import views

urlpatterns = [
    path("", views.index),
]
