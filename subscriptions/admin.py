from django.contrib import admin

from subscriptions.models import StripeWebhookEvent, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user", "plan", "status", "billing_interval",
        "cancel_at_period_end", "updated_at",
    )
    list_filter = ("plan", "status", "billing_interval")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(StripeWebhookEvent)
class StripeWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "event_id", "status", "processed_at")
    list_filter = ("status", "event_type")
    search_fields = ("event_id", "event_type")
    readonly_fields = (
        "event_id", "event_type", "status", "processed_at",
        "last_error", "created_at", "updated_at",
    )
