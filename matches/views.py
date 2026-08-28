from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from matches.forms import MatchForm
from matches.models import Match
from competitions.models import Competition


@login_required
def match_list(request):
    matches = Match.objects.filter(
        owner=request.user
    ).select_related(
        "player"
    )

    status = request.GET.get("status", "").strip()
    player_id = request.GET.get("player", "").strip()
    query = request.GET.get("q", "").strip()
    total_match_count = matches.count()
    has_active_filters = bool(status or player_id or query)

    performance_matches = Match.objects.filter(
        owner=request.user,
        status=Match.Status.COMPLETED,
    ).order_by("-played_at")

    if player_id:
        performance_matches = performance_matches.filter(
            player_id=player_id
        )

    performance_total = performance_matches.count()
    performance_wins = sum(
        1 for match in performance_matches if match.result == "Win"
    )
    performance_losses = performance_total - performance_wins
    performance_sets_won = sum(
        match.player_sets_won or 0 for match in performance_matches
    )
    performance_sets_lost = sum(
        match.opponent_sets_won or 0 for match in performance_matches
    )
    performance_sets_difference = (
        performance_sets_won - performance_sets_lost
    )
    performance_win_rate = (
        round((performance_wins / performance_total) * 100, 1)
        if performance_total
        else 0
    )

    performance_current_streak = 0
    for match in performance_matches:
        if match.result != "Win":
            break
        performance_current_streak += 1

    if status:
        matches = matches.filter(status=status)

    if player_id:
        matches = matches.filter(player_id=player_id)

    if query:
        matches = matches.filter(
            Q(opponent_name__icontains=query)
            | Q(competition__icontains=query)
            | Q(player__first_name__icontains=query)
            | Q(player__last_name__icontains=query)
        )

    paginator = Paginator(matches, 10)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    players = request.user.players.all().order_by(
        "last_name",
        "first_name",
    )

    return render(
        request,
        "matches/match_list.html",
        {
            "page_obj": page_obj,
            "players": players,
            "status_choices": Match.Status.choices,
            "current_status": status,
            "current_player": player_id,
            "current_query": query,
            "total_match_count": total_match_count,
            "has_active_filters": has_active_filters,
            "performance_total": performance_total,
            "performance_wins": performance_wins,
            "performance_losses": performance_losses,
            "performance_win_rate": performance_win_rate,
            "performance_sets_won": performance_sets_won,
            "performance_sets_lost": performance_sets_lost,
            "performance_sets_difference": performance_sets_difference,
            "performance_current_streak": performance_current_streak,
        },
    )


@login_required
def match_detail(request, pk):
    match = get_object_or_404(
        Match.objects.select_related("player"),
        pk=pk,
        owner=request.user,
    )

    return render(
        request,
        "matches/match_detail.html",
        {"match": match},
    )


@login_required
def match_create(request):
    if request.method == "POST":
        form = MatchForm(
            request.POST,
            owner=request.user,
        )

        if form.is_valid():
            match = form.save(commit=False)
            match.owner = request.user
            match.full_clean()
            match.save()

            messages.success(
                request,
                _("Match created successfully."),
            )

            return redirect(
                "matches:detail",
                pk=match.pk,
            )
    else:
        suggested_datetime = timezone.localtime().replace(
            second=0,
            microsecond=0,
        )
        competition_id = request.GET.get("competition", "").strip()
        selected_competition = None
        if competition_id.isdigit():
            selected_competition = Competition.objects.filter(
                owner=request.user,
                pk=competition_id,
            ).first()
        form = MatchForm(
            owner=request.user,
            initial={
                "played_at": suggested_datetime,
                "competition_record": selected_competition,
            },
        )

    return render(
        request,
        "matches/match_form.html",
        {
            "form": form,
            "page_title": _("Add match"),
            "submit_label": _("Create match"),
        },
    )


@login_required
def match_update(request, pk):
    match = get_object_or_404(
        Match,
        pk=pk,
        owner=request.user,
    )

    if request.method == "POST":
        form = MatchForm(
            request.POST,
            instance=match,
            owner=request.user,
        )

        if form.is_valid():
            match = form.save(commit=False)
            match.owner = request.user
            match.full_clean()
            match.save()

            messages.success(
                request,
                _("Match updated successfully."),
            )

            return redirect(
                "matches:detail",
                pk=match.pk,
            )
    else:
        form = MatchForm(
            instance=match,
            owner=request.user,
        )

    return render(
        request,
        "matches/match_form.html",
        {
            "form": form,
            "page_title": _("Edit match"),
            "submit_label": _("Save changes"),
            "match": match,
        },
    )


@login_required
def match_delete(request, pk):
    match = get_object_or_404(
        Match,
        pk=pk,
        owner=request.user,
    )

    if request.method == "POST":
        match.delete()

        messages.success(
            request,
            _("Match deleted successfully."),
        )

        return redirect("matches:list")

    return render(
        request,
        "matches/match_confirm_delete.html",
        {"match": match},
    )
