from django.urls import path

from dashboard import views


app_name = "dashboard"


urlpatterns = [
    path(
        "",
        views.dashboard,
        name="home",
    ),
    path(
        "onboarding/dismiss/",
        views.dismiss_onboarding,
        name="dismiss_onboarding",
    ),
]
