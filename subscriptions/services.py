from datetime import datetime, timezone as datetime_timezone

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from subscriptions.models import StripeWebhookEvent, Subscription


class BillingError(Exception):
    pass


class BillingDisabled(BillingError):
    pass


class BillingConfigurationError(BillingError):
    pass


class BillingProviderError(BillingError):
    pass


class InvalidWebhook(BillingError):
    pass


PAID_PLANS = {
    Subscription.Plan.PROFESSIONAL,
    Subscription.Plan.ORGANIZATION,
}
VALID_INTERVALS = {
    Subscription.BillingInterval.MONTHLY,
    Subscription.BillingInterval.YEARLY,
}


def _stripe():
    try:
        import stripe
    except ImportError as exc:
        raise BillingConfigurationError(
            _("The billing provider is not installed.")
        ) from exc
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def _require_enabled(*, webhook=False):
    if not settings.STRIPE_BILLING_ENABLED:
        raise BillingDisabled(_("Paid subscriptions are not active yet."))

    required = [settings.STRIPE_SECRET_KEY]
    if webhook:
        required.append(settings.STRIPE_WEBHOOK_SECRET)
    if not all(required):
        raise BillingConfigurationError(
            _("Billing is not fully configured.")
        )

    expected = "sk_live_" if settings.STRIPE_LIVE_MODE else "sk_test_"
    if not settings.STRIPE_SECRET_KEY.startswith(expected):
        raise BillingConfigurationError(
            _("Billing credentials do not match the configured mode.")
        )


def _price_id(plan, interval):
    if plan not in PAID_PLANS or interval not in VALID_INTERVALS:
        raise BillingConfigurationError(_("Invalid plan or billing cycle."))

    setting_name = f"STRIPE_PRICE_{plan}_{interval}"
    price_id = getattr(settings, setting_name, "")
    if not price_id:
        raise BillingConfigurationError(
            _("This plan is not available for purchase yet.")
        )
    return price_id


def create_checkout_session(*, user, plan, interval, success_url, cancel_url):
    _require_enabled()
    price_id = _price_id(plan, interval)
    stripe = _stripe()
    subscription, _ = Subscription.objects.get_or_create(user=user)
    metadata = {
        "user_id": str(user.pk),
        "plan": plan,
        "billing_interval": interval,
    }
    parameters = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": str(user.pk),
        "metadata": metadata,
        "subscription_data": {"metadata": metadata},
    }
    if subscription.stripe_customer_id:
        parameters["customer"] = subscription.stripe_customer_id
    else:
        parameters["customer_email"] = user.email
    try:
        return stripe.checkout.Session.create(**parameters)
    except Exception as exc:
        raise BillingProviderError(
            _("The billing service could not start the purchase.")
        ) from exc


def create_billing_portal_session(*, user, return_url):
    _require_enabled()
    subscription, _ = Subscription.objects.get_or_create(user=user)
    if not subscription.stripe_customer_id:
        raise BillingConfigurationError(
            _("There is no billing account to manage yet.")
        )
    try:
        return _stripe().billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=return_url,
        )
    except Exception as exc:
        raise BillingProviderError(
            _("The billing portal is temporarily unavailable.")
        ) from exc


def _value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _as_datetime(value):
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=datetime_timezone.utc)


def _status(value):
    mapping = {
        "incomplete": Subscription.Status.INCOMPLETE,
        "incomplete_expired": Subscription.Status.CANCELED,
        "active": Subscription.Status.ACTIVE,
        "trialing": Subscription.Status.TRIALING,
        "past_due": Subscription.Status.PAST_DUE,
        "unpaid": Subscription.Status.UNPAID,
        "paused": Subscription.Status.PAUSED,
        "canceled": Subscription.Status.CANCELED,
    }
    return mapping.get(value, Subscription.Status.INCOMPLETE)


def _sync_subscription(payload):
    metadata = _value(payload, "metadata", {}) or {}
    user_id = _value(metadata, "user_id")
    stripe_subscription_id = _value(payload, "id")
    stripe_customer_id = _value(payload, "customer")

    subscription = None
    if stripe_subscription_id:
        subscription = Subscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id
        ).first()
    if subscription is None and stripe_customer_id:
        subscription = Subscription.objects.filter(
            stripe_customer_id=stripe_customer_id
        ).first()
    if subscription is None and user_id:
        subscription = Subscription.objects.filter(user_id=user_id).first()
    if subscription is None:
        raise BillingProviderError(_("Subscription owner was not found."))

    items = _value(_value(payload, "items", {}), "data", []) or []
    first_item = items[0] if items else {}
    price_id = _value(_value(first_item, "price", {}), "id", "")
    plan = _value(metadata, "plan", subscription.plan)
    interval = _value(
        metadata, "billing_interval", subscription.billing_interval
    )
    if plan not in PAID_PLANS:
        plan = subscription.plan
    if interval not in VALID_INTERVALS:
        interval = subscription.billing_interval

    subscription.plan = plan
    subscription.billing_interval = interval
    subscription.status = _status(_value(payload, "status", "incomplete"))
    subscription.stripe_customer_id = stripe_customer_id or None
    subscription.stripe_subscription_id = stripe_subscription_id or None
    subscription.stripe_price_id = price_id
    subscription.cancel_at_period_end = bool(
        _value(payload, "cancel_at_period_end", False)
    )
    subscription.trial_ends_at = _as_datetime(_value(payload, "trial_end"))
    subscription.current_period_ends_at = _as_datetime(
        _value(payload, "current_period_end")
    )
    subscription.canceled_at = _as_datetime(_value(payload, "canceled_at"))
    subscription.save()


@transaction.atomic
def process_webhook(payload, signature):
    _require_enabled(webhook=True)
    try:
        event = _stripe().Webhook.construct_event(
            payload, signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as exc:
        raise InvalidWebhook(_("Invalid webhook signature.")) from exc

    event_id = _value(event, "id", "")
    event_type = _value(event, "type", "")
    if not event_id or not event_type:
        raise InvalidWebhook(_("Invalid webhook payload."))

    record, created = StripeWebhookEvent.objects.get_or_create(
        event_id=event_id,
        defaults={"event_type": event_type},
    )
    if not created and record.status in {
        StripeWebhookEvent.Status.PROCESSED,
        StripeWebhookEvent.Status.IGNORED,
    }:
        return record

    try:
        obj = _value(_value(event, "data", {}), "object", {})
        if event_type == "checkout.session.completed":
            user_id = _value(obj, "client_reference_id")
            subscription = Subscription.objects.filter(user_id=user_id).first()
            if subscription:
                subscription.stripe_customer_id = _value(obj, "customer") or None
                subscription.stripe_subscription_id = (
                    _value(obj, "subscription") or None
                )
                subscription.save()
            record.status = StripeWebhookEvent.Status.PROCESSED
        elif event_type in {
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        }:
            _sync_subscription(obj)
            record.status = StripeWebhookEvent.Status.PROCESSED
        else:
            record.status = StripeWebhookEvent.Status.IGNORED
        record.processed_at = timezone.now()
        record.last_error = ""
        record.save()
    except Exception as exc:
        record.status = StripeWebhookEvent.Status.FAILED
        record.last_error = str(exc)[:2000]
        record.save()
        raise BillingProviderError(
            _("The billing event could not be processed.")
        ) from exc
    return record
