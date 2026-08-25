from django.urls import path

from legal import views


app_name = "legal"

urlpatterns = [
    path("privacy/", views.privacy_policy, name="privacy"),
    path("terms/", views.terms_of_use, name="terms"),
]
