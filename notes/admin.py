from django.contrib import admin

from notes.models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "is_pinned",
        "is_archived",
        "updated_at",
        "owner",
    )
    list_filter = ("category", "is_pinned", "is_archived")
    search_fields = ("title", "content", "owner__username")
