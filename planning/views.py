import calendar
from datetime import date, datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from planning.forms import (
    CalendarEventForm,
    EventClassificationForm,
    EventDescriptionForm,
    EventScheduleForm,
)
from planning.models import CalendarEvent
from competitions.models import Competition


@login_required
def event_list(request):
    events = CalendarEvent.objects.filter(
        owner=request.user
    )

    return render(
        request,
        "planning/event_list.html",
        {
            "events": events,
        },
    )


@login_required
def calendar_view(request):
    today = timezone.localdate()

    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        requested_date = date(year, month, 1)
    except (TypeError, ValueError):
        requested_date = date(today.year, today.month, 1)

    year = requested_date.year
    month = requested_date.month

    month_calendar = calendar.Calendar(
        firstweekday=0
    ).monthdatescalendar(
        year,
        month,
    )

    month_start = datetime.combine(
        date(year, month, 1),
        time.min,
    )

    last_day = calendar.monthrange(year, month)[1]

    month_end = datetime.combine(
        date(year, month, last_day),
        time.max,
    )

    current_timezone = timezone.get_current_timezone()

    month_start = timezone.make_aware(
        month_start,
        current_timezone,
    )

    month_end = timezone.make_aware(
        month_end,
        current_timezone,
    )

    events = CalendarEvent.objects.filter(
        owner=request.user,
        start_datetime__lte=month_end,
        end_datetime__gte=month_start,
    ).order_by(
        "start_datetime"
    )

    events_by_date = {}

    for event in events:
        event_date = timezone.localtime(
            event.start_datetime
        ).date()

        events_by_date.setdefault(
            event_date,
            [],
        ).append(event)

    previous_month = (
        month - 1
        if month > 1
        else 12
    )

    previous_year = (
        year
        if month > 1
        else year - 1
    )

    next_month = (
        month + 1
        if month < 12
        else 1
    )

    next_year = (
        year
        if month < 12
        else year + 1
    )

    return render(
        request,
        "planning/calendar.html",
        {
            "calendar_weeks": month_calendar,
            "events_by_date": events_by_date,
            "current_date": today,
            "current_month": requested_date,
            "month_name": date_format(requested_date, "F"),
            "year": year,
            "previous_month": previous_month,
            "previous_year": previous_year,
            "next_month": next_month,
            "next_year": next_year,
            "has_events_anywhere": CalendarEvent.objects.filter(
                owner=request.user
            ).exists(),
        },
    )


def _event_detail_context(event, *, active_section="", invalid_form=None):
    forms = {
        "schedule": EventScheduleForm(instance=event),
        "classification": EventClassificationForm(
            instance=event,
            owner=event.owner,
        ),
        "description": EventDescriptionForm(instance=event),
    }
    if invalid_form is not None and active_section in forms:
        forms[active_section] = invalid_form
    return {
        "event": event,
        "schedule_form": forms["schedule"],
        "classification_form": forms["classification"],
        "description_form": forms["description"],
        "active_section": active_section,
    }


@login_required
def event_detail(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk, owner=request.user)

    return render(
        request,
        "planning/event_detail.html",
        _event_detail_context(event),
    )


@login_required
@require_POST
def event_quick_update(request, pk, section):
    event = get_object_or_404(CalendarEvent, pk=pk, owner=request.user)
    form_classes = {
        "schedule": EventScheduleForm,
        "classification": EventClassificationForm,
        "description": EventDescriptionForm,
    }
    form_class = form_classes.get(section)
    if form_class is None:
        return redirect("planning:detail", pk=event.pk)

    form_kwargs = {"instance": event}
    if section == "classification":
        form_kwargs["owner"] = request.user
    form = form_class(request.POST, **form_kwargs)
    if form.is_valid():
        form.save()
        messages.success(request, _("Event section updated successfully."))
        return redirect(
            f"{reverse('planning:detail', kwargs={'pk': event.pk})}"
            f"#event-{section}"
        )

    return render(
        request,
        "planning/event_detail.html",
        _event_detail_context(
            event,
            active_section=section,
            invalid_form=form,
        ),
        status=400,
    )


@login_required
def event_create(request):
    selected_date = None

    selected_date_value = request.GET.get(
        "date",
        "",
    ).strip()

    if selected_date_value:
        try:
            selected_date = date.fromisoformat(
                selected_date_value
            )
        except ValueError:
            selected_date = None

    if request.method == "POST":
        form = CalendarEventForm(request.POST, owner=request.user)

        if form.is_valid():
            event = form.save(commit=False)
            event.owner = request.user
            event.save()

            return redirect(
                "planning:detail",
                pk=event.pk,
            )
    else:
        suggested_start = timezone.localtime().replace(
            minute=0,
            second=0,
            microsecond=0,
        ) + timedelta(hours=1)
        initial = {
            "start_datetime": suggested_start,
            "end_datetime": suggested_start + timedelta(hours=1),
        }

        competition_id = request.GET.get("competition", "").strip()
        selected_competition = None
        if competition_id.isdigit():
            selected_competition = Competition.objects.filter(
                owner=request.user,
                pk=competition_id,
            ).first()
        if selected_competition:
            initial.update(
                {
                    "competition_record": selected_competition,
                    "event_type": CalendarEvent.EventType.COMPETITION,
                    "title": selected_competition.name,
                    "location": selected_competition.location,
                }
            )

        if selected_date:
            current_timezone = (
                timezone.get_current_timezone()
            )

            start_datetime = timezone.make_aware(
                datetime.combine(
                    selected_date,
                    time(hour=9),
                ),
                current_timezone,
            )

            end_datetime = timezone.make_aware(
                datetime.combine(
                    selected_date,
                    time(hour=10),
                ),
                current_timezone,
            )

            initial = {
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
            }
            if selected_competition:
                initial.update(
                    {
                        "competition_record": selected_competition,
                        "event_type": CalendarEvent.EventType.COMPETITION,
                        "title": selected_competition.name,
                        "location": selected_competition.location,
                    }
                )

        form = CalendarEventForm(
            initial=initial,
            owner=request.user,
        )

    return render(
        request,
        "planning/event_form.html",
        {
            "form": form,
            "page_title": _("Add event"),
            "submit_label": _("Create event"),
            "selected_date": selected_date,
        },
    )


@login_required
def event_update(request, pk):
    event = get_object_or_404(
        CalendarEvent,
        pk=pk,
        owner=request.user,
    )

    if request.method == "POST":
        form = CalendarEventForm(
            request.POST,
            instance=event,
            owner=request.user,
        )

        if form.is_valid():
            form.save()

            return redirect(
                "planning:detail",
                pk=event.pk,
            )
    else:
        form = CalendarEventForm(
            instance=event,
            owner=request.user,
        )

    return render(
        request,
        "planning/event_form.html",
        {
            "form": form,
            "event": event,
            "page_title": _("Edit event"),
            "submit_label": _("Save changes"),
        },
    )


@login_required
def event_delete(request, pk):
    event = get_object_or_404(
        CalendarEvent,
        pk=pk,
        owner=request.user,
    )

    if request.method == "POST":
        event.delete()

        return redirect(
            "planning:list"
        )

    return render(
        request,
        "planning/event_confirm_delete.html",
        {
            "event": event,
        },
    )
