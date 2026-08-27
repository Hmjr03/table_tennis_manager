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


PLAN_CATALOG = (
    PlanDefinition(
        code=Subscription.Plan.STARTER,
        name=_("Starter"),
        audience=_("For individual athletes getting organized"),
        description=_("Essential tools to manage one competitive profile."),
        player_limit=1,
        features=(
            _("Dashboard and calendar"),
            _("Matches and performance"),
            _("Competitions, finances and notes"),
        ),
    ),
    PlanDefinition(
        code=Subscription.Plan.PROFESSIONAL,
        name=_("Professional"),
        audience=_("For athletes and coaches who need more capacity"),
        description=_("A complete workspace for continuous development."),
        player_limit=5,
        features=(
            _("Everything in Starter"),
            _("Up to 5 player profiles"),
            _("Advanced analysis and exports planned"),
        ),
        highlighted=True,
    ),
    PlanDefinition(
        code=Subscription.Plan.ORGANIZATION,
        name=_("Organization"),
        audience=_("For clubs, academies and multidisciplinary teams"),
        description=_("Structured management for growing organizations."),
        player_limit=50,
        features=(
            _("Everything in Professional"),
            _("Up to 50 player profiles"),
            _("Team access and administrative controls planned"),
        ),
    ),
)


def plan_definition(plan_code):
    return next(
        plan for plan in PLAN_CATALOG if plan.code == plan_code
    )
