from django.contrib import admin

from matches.models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "opponent_name",
        "competition",
        "played_at",
        "status",
        "score",
        "result",
        "owner",
    )

    list_filter = (
        "status",
        "best_of",
        "played_at",
    )

    search_fields = (
        "opponent_name",
        "competition",
        "player__first_name",
        "player__last_name",
        "owner__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    date_hierarchy = "played_at"

    ordering = (
        "-played_at",
    )
