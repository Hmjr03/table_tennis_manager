from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from competitions.forms import CompetitionForm
from competitions.models import Competition
from competitions.services import sync_competition_calendar_event
from matches.models import Match
from finances.models import Transaction


@login_required
def competition_list(request):
    competitions = (
        Competition.objects.filter(owner=request.user)
        .prefetch_related("players")
        .annotate(match_count=Count("matches", distinct=True))
    )
    status = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()
    has_active_filters = bool(status or query)
    if status:
        competitions = competitions.filter(status=status)
    if query:
        competitions = competitions.filter(
            Q(name__icontains=query)
            | Q(location__icontains=query)
            | Q(season__icontains=query)
        )

    today = timezone.localdate()
    return render(
        request,
        "competitions/competition_list.html",
        {
            "competitions": competitions,
            "total_count": Competition.objects.filter(owner=request.user).count(),
            "status_choices": Competition.Status.choices,
            "current_status": status,
            "current_query": query,
            "has_active_filters": has_active_filters,
            "upcoming_count": Competition.objects.filter(
                owner=request.user,
                start_date__gte=today,
                status__in=[Competition.Status.PLANNED, Competition.Status.ACTIVE],
            ).count(),
            "completed_count": Competition.objects.filter(
                owner=request.user,
                status=Competition.Status.COMPLETED,
            ).count(),
        },
    )


@login_required
def competition_detail(request, pk):
    competition = get_object_or_404(
        Competition.objects.prefetch_related("players", "events"),
        pk=pk,
        owner=request.user,
    )
    matches = competition.matches.filter(owner=request.user).select_related(
        "player"
    )
    completed_matches = matches.filter(status=Match.Status.COMPLETED)
    wins = completed_matches.filter(
        player_sets_won__gt=F("opponent_sets_won")
    ).count()
    losses = completed_matches.count() - wins
    win_rate = (
        round((wins / completed_matches.count()) * 100, 1)
        if completed_matches.exists()
        else 0
    )
    transactions = competition.transactions.filter(owner=request.user)
    income = transactions.filter(
        transaction_type=Transaction.TransactionType.INCOME,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    expenses = transactions.filter(
        transaction_type=Transaction.TransactionType.EXPENSE,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    return render(
        request,
        "competitions/competition_detail.html",
        {
            "competition": competition,
            "matches": matches[:8],
            "events": competition.events.all()[:8],
            "total_matches": completed_matches.count(),
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "transactions": transactions[:8],
            "competition_income": income,
            "competition_expenses": expenses,
            "competition_balance": income - expenses,
            "linked_notes": competition.linked_notes.filter(
                owner=request.user,
                is_archived=False,
            )[:6],
        },
    )


def _competition_form(request, *, competition=None):
    if request.method == "POST":
        form = CompetitionForm(
            request.POST,
            instance=competition,
            owner=request.user,
        )
        if form.is_valid():
            record = form.save(commit=False)
            record.owner = request.user
            record.full_clean()
            record.save()
            form.save_m2m()
            sync_competition_calendar_event(record)
            messages.success(
                request,
                _("Competition and calendar updated successfully."),
            )
            return redirect("competitions:detail", pk=record.pk)
    else:
        form = CompetitionForm(instance=competition, owner=request.user)
    return render(
        request,
        "competitions/competition_form.html",
        {
            "form": form,
            "competition": competition,
            "page_title": _("Edit competition") if competition else _("Add competition"),
            "submit_label": _("Save changes") if competition else _("Create competition"),
        },
    )


@login_required
def competition_create(request):
    return _competition_form(request)


@login_required
def competition_update(request, pk):
    competition = get_object_or_404(
        Competition,
        pk=pk,
        owner=request.user,
    )
    return _competition_form(request, competition=competition)


@login_required
def competition_delete(request, pk):
    competition = get_object_or_404(
        Competition,
        pk=pk,
        owner=request.user,
    )
    if request.method == "POST":
        competition.delete()
        messages.success(request, _("Competition deleted successfully."))
        return redirect("competitions:list")
    return render(
        request,
        "competitions/competition_confirm_delete.html",
        {"competition": competition},
    )
