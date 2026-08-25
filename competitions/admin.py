from django.contrib import admin

from competitions.models import Competition


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "competition_type", "status", "start_date")
    list_filter = ("competition_type", "status")
    search_fields = ("name", "location", "season", "owner__username")
