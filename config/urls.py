"""
URL Configuration for config project.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

# simple root view that mirrors the health endpoint
# this avoids 404 warnings when hitting '/'


def root_view(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", root_view, name="root"),
    path("admin/", admin.site.urls),
    path("api/", include("game.api.urls")),
]
