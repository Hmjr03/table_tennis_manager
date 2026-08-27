from django.contrib import admin

from subscriptions.models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "updated_at")
    list_filter = ("plan", "status")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
