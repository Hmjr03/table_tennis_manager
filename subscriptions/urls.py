from django.urls import path

from subscriptions import views


app_name = "subscriptions"

urlpatterns = [
    path("", views.plans, name="plans"),
    path("start/", views.create_checkout, name="create_checkout"),
    path("manage/", views.billing_portal, name="billing_portal"),
    path("webhooks/stripe/", views.stripe_webhook, name="stripe_webhook"),
]
