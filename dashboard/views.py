import calendar
from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from finances.models import Transaction
from competitions.models import Competition
from matches.models import Match
from notes.models import Note
from planning.models import CalendarEvent
from players.models import Player
from dashboard.onboarding import onboarding_summary


def _welcome_greeting(current_hour):
    if current_hour < 12:
        return _("Good morning")
    if current_hour < 18:
        return _("Good afternoon")
    return _("Good evening")


@login_required
def dashboard(request):
    user = request.user

    now = timezone.now()
    local_now = timezone.localtime(now)
    today = local_now.date()

    try:
        calendar_year = int(request.GET.get("year", today.year))
        calendar_month_number = int(request.GET.get("month", today.month))
        selected_calendar_month = date(
            calendar_year,
            calendar_month_number,
            1,
        )
    except (TypeError, ValueError):
        selected_calendar_month = today.replace(day=1)

    if selected_calendar_month.month == 1:
        previous_calendar_month = date(
            selected_calendar_month.year - 1,
            12,
            1,
        )
    else:
        previous_calendar_month = date(
            selected_calendar_month.year,
            selected_calendar_month.month - 1,
            1,
        )

    if selected_calendar_month.month == 12:
        next_calendar_month = date(
            selected_calendar_month.year + 1,
            1,
            1,
        )
    else:
        next_calendar_month = date(
            selected_calendar_month.year,
            selected_calendar_month.month + 1,
            1,
        )

    upcoming_events = CalendarEvent.objects.filter(
        owner=user,
        start_datetime__gte=now,
    )

    next_competition = upcoming_events.filter(
        event_type=CalendarEvent.EventType.COMPETITION,
    ).first()

    next_competition_record = Competition.objects.filter(
        owner=user,
        start_date__gte=today,
        status__in=[
            Competition.Status.PLANNED,
            Competition.Status.ACTIVE,
        ],
    ).order_by("start_date", "name").first()

    next_commitment = upcoming_events.exclude(
        event_type=CalendarEvent.EventType.COMPETITION,
    ).first()

    days_until_competition = None
    if next_competition_record:
        days_until_competition = (
            next_competition_record.start_date - today
        ).days
    elif next_competition:
        competition_date = timezone.localtime(
            next_competition.start_datetime
        ).date()
        days_until_competition = (competition_date - today).days

    month_calendar = calendar.Calendar(
        firstweekday=calendar.MONDAY,
    ).monthdatescalendar(
        selected_calendar_month.year,
        selected_calendar_month.month,
    )

    calendar_start = month_calendar[0][0]
    calendar_end = month_calendar[-1][-1]

    calendar_events = CalendarEvent.objects.filter(
        owner=user,
        start_datetime__date__gte=calendar_start,
        start_datetime__date__lte=calendar_end,
    ).order_by("start_datetime")

    events_by_date = {}
    for event in calendar_events:
        event_date = timezone.localtime(
            event.start_datetime
        ).date()
        events_by_date.setdefault(event_date, []).append(event)

    month_transactions = Transaction.objects.filter(
        owner=user,
        date__year=today.year,
        date__month=today.month,
    )

    def transaction_total(queryset):
        return queryset.aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

    monthly_income = transaction_total(
        month_transactions.filter(
            transaction_type=Transaction.TransactionType.INCOME,
        )
    )
    monthly_expenses = transaction_total(
        month_transactions.filter(
            transaction_type=Transaction.TransactionType.EXPENSE,
        )
    )
    monthly_balance = monthly_income - monthly_expenses
    pending_expenses = transaction_total(
        month_transactions.filter(
            transaction_type=Transaction.TransactionType.EXPENSE,
            status=Transaction.Status.PENDING,
        )
    )
    personal_expenses = transaction_total(
        month_transactions.filter(
            transaction_type=Transaction.TransactionType.EXPENSE,
            area=Transaction.Area.PERSONAL,
        )
    )
    professional_expenses = transaction_total(
        month_transactions.filter(
            transaction_type=Transaction.TransactionType.EXPENSE,
            area=Transaction.Area.PROFESSIONAL,
        )
    )

    pinned_notes = Note.objects.filter(
        owner=user,
        is_pinned=True,
        is_archived=False,
    )[:4]

    onboarding = onboarding_summary(user)
    onboarding_requested = request.GET.get("show_onboarding") == "1"
    show_onboarding = (
        not onboarding["is_complete"]
        and (
            user.onboarding_dismissed_at is None
            or onboarding_requested
        )
    )


    players = Player.objects.filter(
        user=user
    )


    matches = Match.objects.filter(
        owner=user
    ).select_related(
        "player"
    )


    completed_matches = matches.filter(
        status=Match.Status.COMPLETED
    ).order_by(
        "-played_at"
    )


    total_matches = completed_matches.count()


    wins = 0
    losses = 0

    sets_won = 0
    sets_lost = 0


    for match in completed_matches:


        if match.result == "Win":

            wins += 1


        elif match.result == "Loss":

            losses += 1



        if match.player_sets_won is not None:

            sets_won += match.player_sets_won



        if match.opponent_sets_won is not None:

            sets_lost += match.opponent_sets_won




    win_rate = 0


    if total_matches:

        win_rate = round(
            (wins / total_matches) * 100,
            1,
        )



    sets_difference = sets_won - sets_lost



    # CURRENT STREAK

    current_streak = 0


    for match in completed_matches:


        if match.result == "Win":

            current_streak += 1


        else:

            break




    context = {

        "welcome_greeting": _welcome_greeting(local_now.hour),
        "display_name": user.get_full_name() or user.username,
        "today": today,
        "next_competition": next_competition,
        "next_competition_record": next_competition_record,
        "days_until_competition": days_until_competition,
        "next_commitment": next_commitment,
        "calendar_weeks": month_calendar,
        "calendar_events_by_date": events_by_date,
        "calendar_month": selected_calendar_month,
        "previous_calendar_month": previous_calendar_month,
        "next_calendar_month": next_calendar_month,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_balance": monthly_balance,
        "pending_expenses": pending_expenses,
        "personal_expenses": personal_expenses,
        "professional_expenses": professional_expenses,
        "pinned_notes": pinned_notes,
        "onboarding": onboarding,
        "show_onboarding": show_onboarding,
        "onboarding_was_dismissed": (
            not onboarding["is_complete"]
            and user.onboarding_dismissed_at is not None
            and not onboarding_requested
        ),


        "players_count": players.count(),


        "matches_played": total_matches,


        "wins": wins,


        "losses": losses,


        "win_rate": win_rate,


        "sets_won": sets_won,


        "sets_lost": sets_lost,


        "sets_difference": sets_difference,


        "current_streak": current_streak,


    }



    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )


@login_required
@require_POST
def dismiss_onboarding(request):
    request.user.onboarding_dismissed_at = timezone.now()
    request.user.save(update_fields=["onboarding_dismissed_at"])
    return redirect("dashboard:home")
