from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from matches.models import Match
from players.models import Player


@login_required
def dashboard(request):

    user = request.user


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



    recent_matches = completed_matches[:5]



    # CURRENT STREAK

    current_streak = 0


    for match in completed_matches:


        if match.result == "Win":

            current_streak += 1


        else:

            break




    context = {


        "players_count": players.count(),


        "matches_played": total_matches,


        "wins": wins,


        "losses": losses,


        "win_rate": win_rate,


        "sets_won": sets_won,


        "sets_lost": sets_lost,


        "sets_difference": sets_difference,


        "current_streak": current_streak,


        "recent_matches": recent_matches,

    }



    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )
