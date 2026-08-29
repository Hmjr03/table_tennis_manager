from django.urls import reverse
from django.utils.translation import gettext as _

from matches.models import Match
from planning.models import CalendarEvent
from players.models import Player


def onboarding_summary(user):
    player_exists = Player.objects.filter(user=user).exists()

    steps = (
        {
            "key": "player",
            "title": _("Create your first player"),
            "description": _(
                "Build the athlete profile that will connect matches and analysis."
            ),
            "url": reverse("players:create"),
            "completed": player_exists,
            "available": True,
        },
        {
            "key": "commitment",
            "title": _("Schedule your first commitment"),
            "description": _(
                "Add a training session, meeting, trip or personal commitment."
            ),
            "url": reverse("planning:create"),
            "completed": CalendarEvent.objects.filter(owner=user)
            .exclude(event_type=CalendarEvent.EventType.COMPETITION)
            .exists(),
            "available": True,
        },
        {
            "key": "match",
            "title": _("Record your first match"),
            "description": _(
                "Start building a reliable history of results and performance."
            ),
            "url": reverse("matches:create"),
            "completed": Match.objects.filter(owner=user).exists(),
            "available": player_exists,
        },
    )
    completed_count = sum(step["completed"] for step in steps)
    total_count = len(steps)

    return {
        "steps": steps,
        "completed_count": completed_count,
        "total_count": total_count,
        "progress_percent": round(completed_count / total_count * 100),
        "is_complete": completed_count == total_count,
    }
