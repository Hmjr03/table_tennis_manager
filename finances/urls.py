from django.urls import path

from finances import views


app_name = "finances"

urlpatterns = [
    path("", views.transaction_list, name="list"),
    path("create/", views.transaction_create, name="create"),
    path("<int:pk>/edit/", views.transaction_update, name="update"),
    path("<int:pk>/delete/", views.transaction_delete, name="delete"),
]
