from django.urls import path

from planning import views


app_name = "planning"


urlpatterns = [
    path(
        "",
        views.event_list,
        name="list",
    ),
    path(
        "calendar/",
        views.calendar_view,
        name="calendar",
    ),
    path(
        "create/",
        views.event_create,
        name="create",
    ),
    path(
        "<int:pk>/",
        views.event_detail,
        name="detail",
    ),
    path(
        "<int:pk>/edit/",
        views.event_update,
        name="edit",
    ),
    path(
        "<int:pk>/delete/",
        views.event_delete,
        name="delete",
    ),
]
