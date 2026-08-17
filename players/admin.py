from django.contrib import admin

from players.models import Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "user",
        "hand",
        "ranking",
        "created_at",
    )
    list_filter = (
        "hand",
    )
    search_fields = (
        "first_name",
        "last_name",
        "user__username",
    )

