from django.urls import path

from subscriptions import views


app_name = "subscriptions"

urlpatterns = [
    path("", views.plans, name="plans"),
]
