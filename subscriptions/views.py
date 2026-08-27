from django.shortcuts import render

from subscriptions.catalog import PLAN_CATALOG
from subscriptions.models import Subscription


def plans(request):
    current_plan = None
    if request.user.is_authenticated:
        current_plan = (
            Subscription.objects.filter(user=request.user)
            .values_list("plan", flat=True)
            .first()
            or Subscription.Plan.STARTER
        )

    return render(
        request,
        "subscriptions/plans.html",
        {
            "plans": PLAN_CATALOG,
            "current_plan": current_plan,
        },
    )
