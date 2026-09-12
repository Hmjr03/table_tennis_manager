from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpResponse, HttpResponsePermanentRedirect, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


ANDROID_PACKAGE_ID = "com.escolatmmanager.app"
ANDROID_UPLOAD_CERTIFICATE_SHA256 = (
    "01:6F:C6:5F:DD:90:93:4B:A4:BD:25:32:37:86:DD:74:"
    "E7:D5:88:2B:5C:32:9B:A8:D7:0E:38:A9:E9:97:FA:3E"
)


@require_GET
@never_cache
def health_check(request):
    """Backward-compatible readiness endpoint."""
    return readiness_check(request)


@require_GET
def favicon(request):
    return HttpResponsePermanentRedirect(static("icons/favicon.ico"))


@require_GET
def android_asset_links(request):
    """Authorize the signed ETM Manager Android app to open this domain."""
    response = JsonResponse(
        [
            {
                "relation": [
                    "delegate_permission/common.handle_all_urls",
                ],
                "target": {
                    "namespace": "android_app",
                    "package_name": ANDROID_PACKAGE_ID,
                    "sha256_cert_fingerprints": [
                        ANDROID_UPLOAD_CERTIFICATE_SHA256,
                    ],
                },
            }
        ],
        safe=False,
    )
    response["Cache-Control"] = "public, max-age=3600"
    return response


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
            "name": "ETM Manager",
            "short_name": "ETM Manager",
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
