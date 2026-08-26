from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from matches.models import Match
from players.models import Player


@login_required
def analysis(request):

    matches = (
        Match.objects.filter(
            owner=request.user,
            status=Match.Status.COMPLETED,
        )
        .select_related("player")
        .order_by("-played_at")
    )


    selected_player = request.GET.get("player")


    if selected_player:
        matches = matches.filter(
            player_id=selected_player
        )


    total_matches = matches.count()


    wins = 0
    losses = 0

    sets_won = 0
    sets_lost = 0


    for match in matches:

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



    #
    # RECENT FORM
    #

    recent_matches = list(
        matches[:5]
    )


    form = []

    recent_wins = 0
    recent_losses = 0


    for match in recent_matches:

        if match.result == "Win":

            form.append("W")
            recent_wins += 1


        elif match.result == "Loss":

            form.append("L")
            recent_losses += 1



    recent_total = (
        recent_wins +
        recent_losses
    )


    recent_win_rate = 0


    if recent_total:

        recent_win_rate = round(
            (recent_wins / recent_total) * 100,
            1,
        )



    #
    # WINNING STREAK
    #

    chronological_matches = list(
        matches.order_by(
            "played_at"
        )
    )


    longest_win_streak = 0
    current_counter = 0


    for match in chronological_matches:


        if match.result == "Win":

            current_counter += 1


            if current_counter > longest_win_streak:

                longest_win_streak = current_counter


        else:

            current_counter = 0



    current_streak = 0


    for match in reversed(
        chronological_matches
    ):


        if match.result == "Win":

            current_streak += 1


        else:

            break



    if current_streak:

        current_streak_type = "Win"

    elif chronological_matches:

        current_streak_type = "Loss"

    else:

        current_streak_type = "None"



    #
    # PLAYERS FILTER
    #

    players = (
        Player.objects.filter(
            user=request.user
        )
        .order_by(
            "last_name",
            "first_name",
        )
    )



    context = {

        "total_matches": total_matches,

        "wins": wins,

        "losses": losses,

        "win_rate": win_rate,


        "sets_won": sets_won,

        "sets_lost": sets_lost,

        "sets_difference": sets_difference,


        "recent_matches": recent_matches,

        "form": form,

        "recent_wins": recent_wins,

        "recent_losses": recent_losses,

        "recent_win_rate": recent_win_rate,


        "current_streak": current_streak,

        "current_streak_type": current_streak_type,

        "longest_win_streak": longest_win_streak,


        "players": players,

        "selected_player": selected_player,

    }


    return render(
        request,
        "matches/match_analysis.html",
        context,
    )


@login_required
def dashboard(request):
    # Backward-compatible alias for saved links. The feature now belongs
    # to the Matches section and renders its integrated analysis page.
    return analysis(request)
