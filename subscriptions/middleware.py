from django.conf import settings
from django.shortcuts import redirect


class SubscriptionAccessMiddleware:
    EXEMPT_PREFIXES = (
        "/accounts/",
        "/admin/",
        "/health/",
        "/i18n/",
        "/legal/",
        "/plans/",
        "/static/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._requires_subscription(request):
            return redirect("subscriptions:plans")
        return self.get_response(request)

    def _requires_subscription(self, request):
        if not settings.SUBSCRIPTION_ACCESS_ENFORCED:
            return False
        if not request.user.is_authenticated:
            return False
        if request.path == "/" or request.path.startswith(self.EXEMPT_PREFIXES):
            return False
        try:
            subscription = request.user.subscription
        except AttributeError:
            return True
        return not subscription.has_product_access
