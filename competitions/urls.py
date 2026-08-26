from django.urls import path

from competitions import views


app_name = "competitions"

urlpatterns = [
    path("", views.competition_list, name="list"),
    path("add/", views.competition_create, name="create"),
    path("<int:pk>/", views.competition_detail, name="detail"),
    path("<int:pk>/edit/", views.competition_update, name="update"),
    path("<int:pk>/delete/", views.competition_delete, name="delete"),
]
