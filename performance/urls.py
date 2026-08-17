from django.urls import path

from performance import views


app_name = "performance"


urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
]
