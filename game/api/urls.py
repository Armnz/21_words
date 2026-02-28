from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("v1/sessions/", views.SessionCreateView.as_view(), name="session_create"),
    path("v1/sessions/<uuid:session_id>/", views.SessionDetailView.as_view(), name="session_detail"),
    path(
        "v1/sessions/<uuid:session_id>/attempt/",
        views.SessionAttemptView.as_view(),
        name="session_attempt",
    ),
    path(
        "v1/sessions/<uuid:session_id>/publish/",
        views.SessionPublishView.as_view(),
        name="session_publish",
    ),
    path("v1/leaderboard/", views.LeaderboardView.as_view(), name="leaderboard"),
]
