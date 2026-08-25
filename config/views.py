from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@require_GET
@never_cache
def health_check(request):
    """Backward-compatible readiness endpoint."""
    return readiness_check(request)


@require_GET
@never_cache
def liveness_check(request):
    """Confirm that the web process can answer requests."""
    return JsonResponse({"status": "ok"})


@require_GET
@never_cache
def readiness_check(request):
    """Confirm that the application and database are ready."""
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except OperationalError:
        return JsonResponse(
            {"status": "unavailable"},
            status=503,
        )

    return JsonResponse({"status": "ok"})


@require_GET
def pwa_manifest(request):
    response = JsonResponse(
        {
            "id": "/",
            "name": "Table Tennis Manager",
            "short_name": "TT Manager",
            "description": _(
                "Manage athletes, matches, competitions and performance."
            ),
            "lang": getattr(request, "LANGUAGE_CODE", "en"),
            "start_url": reverse("dashboard:home"),
            "scope": "/",
            "display": "standalone",
            "display_override": ["standalone", "minimal-ui"],
            "orientation": "any",
            "background_color": "#f4f7fc",
            "theme_color": "#2563eb",
            "categories": ["sports", "productivity", "lifestyle"],
            "icons": [
                {
                    "src": static("icons/icon-192.png"),
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any",
                },
                {
                    "src": static("icons/icon-512.png"),
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any",
                },
                {
                    "src": static("icons/icon-maskable-512.png"),
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "maskable",
                },
            ],
            "shortcuts": [
                {
                    "name": _("Dashboard"),
                    "url": reverse("dashboard:home"),
                    "icons": [
                        {
                            "src": static("icons/icon-192.png"),
                            "sizes": "192x192",
                        }
                    ],
                },
                {
                    "name": _("Add match"),
                    "url": reverse("matches:create"),
                    "icons": [
                        {
                            "src": static("icons/icon-192.png"),
                            "sizes": "192x192",
                        }
                    ],
                },
                {
                    "name": _("Calendar"),
                    "url": reverse("planning:calendar"),
                    "icons": [
                        {
                            "src": static("icons/icon-192.png"),
                            "sizes": "192x192",
                        }
                    ],
                },
            ],
        }
    )
    response["Content-Type"] = "application/manifest+json"
    response["Cache-Control"] = "public, max-age=3600"
    return response


@require_GET
def service_worker(request):
    response = render(
        request,
        "pwa/service-worker.js",
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@require_GET
def offline_page(request):
    response = render(request, "pwa/offline.html")
    response["Cache-Control"] = "public, max-age=3600"
    return response
