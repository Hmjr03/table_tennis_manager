from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from subscriptions.catalog import PLAN_CATALOG
from subscriptions.models import Subscription
from subscriptions.services import (
    BillingError,
    InvalidWebhook,
    create_billing_portal_session,
    create_checkout_session,
    process_webhook,
)


def plans(request):
    current_plan = None
    current_subscription = None
    if request.user.is_authenticated:
        current_subscription = Subscription.objects.filter(
            user=request.user
        ).first()
        current_plan = (
            current_subscription.plan
            if current_subscription
            else Subscription.Plan.STARTER
        )

    return render(
        request,
        "subscriptions/plans.html",
        {
            "plans": PLAN_CATALOG,
            "current_plan": current_plan,
            "current_subscription": current_subscription,
            "billing_enabled": settings.STRIPE_BILLING_ENABLED,
        },
    )


@login_required
@require_POST
def create_checkout(request):
    try:
        session = create_checkout_session(
            user=request.user,
            plan=request.POST.get("plan", ""),
            interval=request.POST.get("interval", ""),
            success_url=request.build_absolute_uri(
                reverse("subscriptions:plans") + "?payment=success"
            ),
            cancel_url=request.build_absolute_uri(
                reverse("subscriptions:plans") + "?payment=canceled"
            ),
        )
    except BillingError as exc:
        messages.error(request, str(exc))
        return redirect("subscriptions:plans")
    return redirect(session.url)


@login_required
@require_POST
def billing_portal(request):
    try:
        session = create_billing_portal_session(
            user=request.user,
            return_url=request.build_absolute_uri(
                reverse("subscriptions:plans")
            ),
        )
    except BillingError as exc:
        messages.error(request, str(exc))
        return redirect("subscriptions:plans")
    return redirect(session.url)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    try:
        process_webhook(request.body, request.headers.get("Stripe-Signature", ""))
    except InvalidWebhook:
        return HttpResponse(_("Invalid webhook."), status=400)
    except BillingError:
        return HttpResponse(_("Billing service unavailable."), status=503)
    return HttpResponse(status=200)
