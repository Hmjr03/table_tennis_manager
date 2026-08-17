from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from matches.forms import MatchForm
from matches.models import Match


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
                "Match created successfully.",
            )

            return redirect(
                "matches:detail",
                pk=match.pk,
            )
    else:
        form = MatchForm(
            owner=request.user,
        )

    return render(
        request,
        "matches/match_form.html",
        {
            "form": form,
            "page_title": "Add match",
            "submit_label": "Create match",
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
                "Match updated successfully.",
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
            "page_title": "Edit match",
            "submit_label": "Save changes",
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
            "Match deleted successfully.",
        )

        return redirect("matches:list")

    return render(
        request,
        "matches/match_confirm_delete.html",
        {"match": match},
    )
