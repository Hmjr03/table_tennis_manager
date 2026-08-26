from django.contrib import admin

from finances.models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "description",
        "transaction_type",
        "area",
        "amount",
        "status",
        "owner",
    )
    list_filter = ("transaction_type", "area", "status", "date")
    search_fields = ("description", "owner__username", "owner__email")
