from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
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
