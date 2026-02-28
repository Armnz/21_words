"""
URL Configuration for config project.
"""

from django.urls import include, path

urlpatterns = [
    path("api/", include("game.api.urls")),
]
