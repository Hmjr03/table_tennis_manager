from datetime import datetime, time

from django.db import transaction
from django.utils import timezone

from planning.models import CalendarEvent


@transaction.atomic
def sync_competition_calendar_event(competition):
    """Create or update only the calendar event managed by a competition."""
    current_timezone = timezone.get_current_timezone()
    end_date = competition.end_date or competition.start_date
    start_datetime = timezone.make_aware(
        datetime.combine(competition.start_date, time(hour=9)),
        current_timezone,
    )
    end_datetime = timezone.make_aware(
        datetime.combine(end_date, time(hour=18)),
        current_timezone,
    )

    event, created = CalendarEvent.objects.update_or_create(
        competition_record=competition,
        is_competition_sync=True,
        defaults={
            "owner": competition.owner,
            "title": competition.name,
            "event_type": CalendarEvent.EventType.COMPETITION,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "location": competition.location,
        },
    )
    if created:
        event.priority = CalendarEvent.Priority.HIGH
        event.save(update_fields=["priority", "updated_at"])
    return event
