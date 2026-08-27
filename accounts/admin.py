from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Table Tennis Manager",
            {
                "fields": (
                    "role",
                    "terms_accepted_at",
                    "privacy_notice_acknowledged_at",
                    "legal_documents_version",
                    "onboarding_dismissed_at",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Table Tennis Manager",
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                )
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    readonly_fields = (
        "terms_accepted_at",
        "privacy_notice_acknowledged_at",
        "legal_documents_version",
        "onboarding_dismissed_at",
    )
