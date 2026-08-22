from django.contrib import admin
from django.urls import include, path

from accounts import views


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "",
        views.home,
        name="home",
    ),
    path(
        "accounts/",
        include("accounts.urls"),
    ),
    path(
        "dashboard/",
        include("dashboard.urls"),
    ),
    path(
        "players/",
        include("players.urls"),
    ),
    path(
        "matches/",
        include("matches.urls"),
    ),
    path(
        "performance/",
        include("performance.urls"),
    ),
    path(
        "planning/",
        include(
            "planning.urls",
            namespace="planning",
        ),
    ),
]
