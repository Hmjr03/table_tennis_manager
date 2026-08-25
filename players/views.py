from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Count, F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from matches.models import Match
from players.forms import PlayerForm
from players.models import Player


@login_required
def player_list(request):
    players = Player.objects.filter(
        user=request.user
    )

    total_players = players.count()
    ranked_players = players.filter(
        Q(world_ranking__gt=0) | Q(national_ranking__gt=0)
    ).count()
    profiles_to_complete = players.filter(
        Q(world_ranking=0, national_ranking=0)
        | Q(date_of_birth__isnull=True)
    ).count()

    return render(
        request,
        "players/player_list.html",
        {
            "players": players,
            "total_players": total_players,
            "ranked_players": ranked_players,
            "profiles_to_complete": profiles_to_complete,
        },
    )


@login_required
def player_detail(request, pk):
    player = get_object_or_404(
        Player,
        pk=pk,
        user=request.user,
    )

    completed_matches = player.matches_as_player.filter(
        owner=request.user,
        status=Match.Status.COMPLETED,
    )
    total_matches = completed_matches.count()
    wins = completed_matches.filter(
        player_sets_won__gt=F("opponent_sets_won")
    ).count()
    losses = total_matches - wins
    win_rate = round((wins / total_matches) * 100, 1) if total_matches else 0
    loss_rate = round((losses / total_matches) * 100, 1) if total_matches else 0

    league_rows = completed_matches.values("competition").annotate(
        matches_played=Count("id"),
        wins=Count("id", filter=Q(player_sets_won__gt=F("opponent_sets_won"))),
    ).order_by("-matches_played", "competition")
    league_stats = []
    for row in league_rows:
        league_losses = row["matches_played"] - row["wins"]
        league_stats.append(
            {
                "name": row["competition"] or _("Unspecified league"),
                "matches_played": row["matches_played"],
                "wins": row["wins"],
                "losses": league_losses,
                "win_rate": round((row["wins"] / row["matches_played"]) * 100, 1),
                "loss_rate": round((league_losses / row["matches_played"]) * 100, 1),
            }
        )

    return render(
        request,
        "players/player_detail.html",
        {
            "player": player,
            "total_matches": total_matches,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "loss_rate": loss_rate,
            "league_stats": league_stats,
            "recent_matches": completed_matches[:5],
        },
    )


@login_required
def player_create(request):
    if request.method == "POST":
        form = PlayerForm(request.POST)

        if form.is_valid():
            player = form.save(commit=False)
            player.user = request.user
            player.save()

            return redirect(
                "players:detail",
                pk=player.pk,
            )
    else:
        form = PlayerForm()

    return render(
        request,
        "players/player_form.html",
        {
            "form": form,
            "page_title": _("Add player"),
            "submit_label": _("Create player"),
        },
    )


@login_required
def player_update(request, pk):
    player = get_object_or_404(
        Player,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        form = PlayerForm(
            request.POST,
            instance=player,
        )

        if form.is_valid():
            form.save()

            return redirect(
                "players:detail",
                pk=player.pk,
            )
    else:
        form = PlayerForm(instance=player)

    return render(
        request,
        "players/player_form.html",
        {
            "form": form,
            "player": player,
            "page_title": _("Edit player"),
            "submit_label": _("Save changes"),
        },
    )


@login_required
def player_delete(request, pk):
    player = get_object_or_404(
        Player,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        player.delete()

        return redirect("players:list")

    return render(
        request,
        "players/player_confirm_delete.html",
        {
            "player": player,
        },
    )
