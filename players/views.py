from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from players.forms import PlayerForm
from players.models import Player


@login_required
def player_list(request):
    players = Player.objects.filter(
        user=request.user
    )

    return render(
        request,
        "players/player_list.html",
        {
            "players": players,
        },
    )


@login_required
def player_detail(request, pk):
    player = get_object_or_404(
        Player,
        pk=pk,
        user=request.user,
    )

    return render(
        request,
        "players/player_detail.html",
        {
            "player": player,
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
            "page_title": "Add player",
            "submit_label": "Create player",
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
            "page_title": "Edit player",
            "submit_label": "Save changes",
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

