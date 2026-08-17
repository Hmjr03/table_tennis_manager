from django.urls import path

from players import views


app_name = "players"


urlpatterns = [
    path(
        "",
        views.player_list,
        name="list",
    ),
    path(
        "create/",
        views.player_create,
        name="create",
    ),
    path(
        "<int:pk>/",
        views.player_detail,
        name="detail",
    ),
    path(
        "<int:pk>/edit/",
        views.player_update,
        name="edit",
    ),
    path(
        "<int:pk>/delete/",
        views.player_delete,
        name="delete",
    ),
]

