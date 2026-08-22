import calendar
from datetime import date, datetime, time

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from planning.forms import CalendarEventForm
from planning.models import CalendarEvent


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
            "month_name": requested_date.strftime("%B"),
            "year": year,
            "previous_month": previous_month,
            "previous_year": previous_year,
            "next_month": next_month,
            "next_year": next_year,
        },
    )


@login_required
def event_detail(request, pk):
    event = get_object_or_404(
        CalendarEvent,
        pk=pk,
        owner=request.user,
    )

    return render(
        request,
        "planning/event_detail.html",
        {
            "event": event,
        },
    )


@login_required
def event_create(request):
    if request.method == "POST":
        form = CalendarEventForm(request.POST)

        if form.is_valid():
            event = form.save(commit=False)
            event.owner = request.user
            event.save()

            return redirect(
                "planning:detail",
                pk=event.pk,
            )
    else:
        form = CalendarEventForm()

    return render(
        request,
        "planning/event_form.html",
        {
            "form": form,
            "page_title": "Add event",
            "submit_label": "Create event",
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
        )

        if form.is_valid():
            form.save()

            return redirect(
                "planning:detail",
                pk=event.pk,
            )
    else:
        form = CalendarEventForm(
            instance=event
        )

    return render(
        request,
        "planning/event_form.html",
        {
            "form": form,
            "event": event,
            "page_title": "Edit event",
            "submit_label": "Save changes",
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
