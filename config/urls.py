from django.contrib import admin
from django.urls import include, path

from accounts import views
from config.views import health_check


urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("i18n/", include("django.conf.urls.i18n")),
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
    path(
        "finances/",
        include("finances.urls", namespace="finances"),
    ),
    path(
        "notes/",
        include("notes.urls", namespace="notes"),
    ),
    path(
        "competitions/",
        include("competitions.urls", namespace="competitions"),
    ),
    path("legal/", include("legal.urls", namespace="legal")),
]
