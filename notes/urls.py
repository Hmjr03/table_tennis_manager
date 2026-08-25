from django.urls import path

from notes import views


app_name = "notes"

urlpatterns = [
    path("", views.note_list, name="list"),
    path("create/", views.note_create, name="create"),
    path("<int:pk>/edit/", views.note_update, name="update"),
    path("<int:pk>/delete/", views.note_delete, name="delete"),
    path("<int:pk>/pin/", views.note_toggle_pin, name="toggle_pin"),
    path("<int:pk>/archive/", views.note_toggle_archive, name="toggle_archive"),
]
