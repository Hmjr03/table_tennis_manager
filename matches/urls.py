from django.urls import path

from matches import views
from performance import views as performance_views


app_name = "matches"

urlpatterns = [
    path(
        "",
        views.match_list,
        name="list",
    ),
    path(
        "add/",
        views.match_create,
        name="create",
    ),
    path(
        "analysis/",
        performance_views.analysis,
        name="analysis",
    ),
    path(
        "<int:pk>/",
        views.match_detail,
        name="detail",
    ),
    path(
        "<int:pk>/edit/",
        views.match_update,
        name="update",
    ),
    path(
        "<int:pk>/delete/",
        views.match_delete,
        name="delete",
    ),
]
