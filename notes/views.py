from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _

from notes.forms import NoteForm
from notes.models import Note
from competitions.models import Competition


@login_required
def note_list(request):
    show_archived = request.GET.get("archived") == "1"
    category = request.GET.get("category", "").strip()
    query = request.GET.get("q", "").strip()

    notes = Note.objects.filter(
        owner=request.user,
        is_archived=show_archived,
    )

    if category in Note.Category.values:
        notes = notes.filter(category=category)
    if query:
        notes = notes.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    paginator = Paginator(notes, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "notes/note_list.html",
        {
            "page_obj": page_obj,
            "category_choices": Note.Category.choices,
            "current_category": category,
            "current_query": query,
            "show_archived": show_archived,
        },
    )


@login_required
def note_create(request):
    if request.method == "POST":
        form = NoteForm(request.POST, owner=request.user)
        if form.is_valid():
            note = form.save(commit=False)
            note.owner = request.user
            note.save()
            messages.success(request, _("Note created successfully."))
            return redirect("notes:list")
    else:
        competition_id = request.GET.get("competition", "").strip()
        selected_competition = None
        if competition_id.isdigit():
            selected_competition = Competition.objects.filter(
                owner=request.user,
                pk=competition_id,
            ).first()
        form = NoteForm(
            owner=request.user,
            initial={
                "competition_record": selected_competition,
                "category": Note.Category.COMPETITION if selected_competition else None,
            },
        )

    return render(
        request,
        "notes/note_form.html",
        {"form": form, "page_title": _("Add note"), "submit_label": _("Save note")},
    )


@login_required
def note_update(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    if request.method == "POST":
        form = NoteForm(request.POST, instance=note, owner=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Note updated successfully."))
            return redirect("notes:list")
    else:
        form = NoteForm(instance=note, owner=request.user)

    return render(
        request,
        "notes/note_form.html",
        {"form": form, "page_title": _("Edit note"), "submit_label": _("Save changes"), "note": note},
    )


@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    if request.method == "POST":
        note.delete()
        messages.success(request, _("Note deleted successfully."))
        return redirect("notes:list")

    return render(
        request,
        "notes/note_confirm_delete.html",
        {"note": note},
    )


@login_required
@require_POST
def note_toggle_pin(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    note.is_pinned = not note.is_pinned
    note.save(update_fields=["is_pinned", "updated_at"])
    messages.success(
        request,
        _("Note pinned to dashboard.") if note.is_pinned else _("Note unpinned."),
    )
    return redirect("notes:list")


@login_required
@require_POST
def note_toggle_archive(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    note.is_archived = not note.is_archived
    if note.is_archived:
        note.is_pinned = False
    note.save(update_fields=["is_archived", "is_pinned", "updated_at"])
    messages.success(
        request,
        _("Note archived.") if note.is_archived else _("Note restored."),
    )
    return redirect("notes:list")
