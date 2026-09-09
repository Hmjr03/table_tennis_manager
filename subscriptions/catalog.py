from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from subscriptions.models import Subscription


@dataclass(frozen=True)
class PlanDefinition:
    code: str
    name: str
    audience: str
    description: str
    player_limit: int | None
    features: tuple[str, ...]
    highlighted: bool = False
    monthly_price: str | None = None
    yearly_price: str | None = None
    yearly_savings: str | None = None
    trial_available: bool = False


PLAN_CATALOG = (
    PlanDefinition(
        code=Subscription.Plan.STARTER,
        name=_("Individual"),
        audience=_("For individual athletes getting organized"),
        description=_("Essential tools to manage one competitive profile."),
        player_limit=1,
        features=(
            _("Dashboard and calendar"),
            _("Matches and performance"),
            _("Competitions, finances and notes"),
        ),
        monthly_price=_("R$ 14.90/month"),
        yearly_price=_("R$ 149/year"),
        yearly_savings=_("save R$ 29.80"),
        trial_available=True,
    ),
    PlanDefinition(
        code=Subscription.Plan.PROFESSIONAL,
        name=_("Professional"),
        audience=_("For athletes and coaches who need more capacity"),
        description=_("A complete workspace for continuous development."),
        player_limit=5,
        features=(
            _("Everything in Individual"),
            _("Up to 5 player profiles"),
            _("Expanded capacity for coaches and professionals"),
        ),
        highlighted=True,
        monthly_price=_("R$ 29.90/month"),
        yearly_price=_("R$ 299/year"),
        yearly_savings=_("save R$ 59.80"),
    ),
    PlanDefinition(
        code=Subscription.Plan.ORGANIZATION,
        name=_("Organization"),
        audience=_("For clubs, academies and multidisciplinary teams"),
        description=_("Structured management for growing organizations."),
        player_limit=300,
        features=(
            _("Everything in Professional"),
            _("Up to 300 player profiles"),
            _("Centralized sporting and administrative history"),
        ),
        monthly_price=_("R$ 99.90/month"),
        yearly_price=_("R$ 999/year"),
        yearly_savings=_("save R$ 199.80"),
    ),
)


def plan_definition(plan_code):
    return next(
        plan for plan in PLAN_CATALOG if plan.code == plan_code
    )
