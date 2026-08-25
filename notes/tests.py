from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class NoteFormTests(TestCase):
    def test_note_form_requires_meaningful_title_and_content(self):
        form = NoteForm(
            data={
                "title": "AB",
                "category": Note.Category.GENERAL,
                "content": "   ",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        self.assertIn("content", form.errors)


class NoteViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notes_user",
            email="notes@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="other_notes_user",
            email="other-notes@example.com",
            password="StrongPassword123!",
        )
        self.client.force_login(self.user)

    def create_note(self, *, title, owner=None, **kwargs):
        return Note.objects.create(
            owner=owner or self.user,
            title=title,
            content=kwargs.pop("content", "Useful note content"),
            category=kwargs.pop("category", Note.Category.GENERAL),
            **kwargs,
        )

    def test_notes_require_authentication(self):
        self.client.logout()
        response = self.client.get(reverse("notes:list"))
        self.assertEqual(response.status_code, 302)

    def test_notes_page_isolated_by_owner(self):
        self.create_note(title="Visible tactical note")
        self.create_note(title="Private tactical note", owner=self.other_user)

        response = self.client.get(reverse("notes:list"))

        self.assertContains(response, "Visible tactical note")
        self.assertNotContains(response, "Private tactical note")

    def test_search_finds_title_and_content(self):
        self.create_note(title="Serve practice", content="Improve backspin variation")
        self.create_note(title="Unrelated note", content="Hotel reservation")

        response = self.client.get(reverse("notes:list"), {"q": "backspin"})

        self.assertContains(response, "Serve practice")
        self.assertNotContains(response, "Unrelated note")

    def test_create_note_assigns_authenticated_owner(self):
        response = self.client.post(
            reverse("notes:create"),
            {
                "title": "Match preparation",
                "category": Note.Category.COMPETITION,
                "content": "Review the opponent's receive position.",
                "is_pinned": "on",
            },
        )

        self.assertRedirects(response, reverse("notes:list"))
        note = Note.objects.get()
        self.assertEqual(note.owner, self.user)
        self.assertTrue(note.is_pinned)

    def test_note_form_uses_professional_context_navigation(self):
        response = self.client.get(reverse("notes:create"))

        self.assertContains(response, 'class="context-navigation"')
        self.assertContains(response, reverse("notes:list"))
        self.assertContains(response, "Back to notes")

    def test_pin_action_requires_post(self):
        note = self.create_note(title="Important reminder")

        response = self.client.get(reverse("notes:toggle_pin", args=[note.pk]))

        self.assertEqual(response.status_code, 405)
        note.refresh_from_db()
        self.assertFalse(note.is_pinned)

    def test_archiving_note_also_unpins_it(self):
        note = self.create_note(title="Completed decision", is_pinned=True)

        response = self.client.post(
            reverse("notes:toggle_archive", args=[note.pk])
        )

        self.assertRedirects(response, reverse("notes:list"))
        note.refresh_from_db()
        self.assertTrue(note.is_archived)
        self.assertFalse(note.is_pinned)

    def test_user_cannot_edit_another_users_note(self):
        note = self.create_note(title="Private note", owner=self.other_user)

        response = self.client.get(reverse("notes:update", args=[note.pk]))

        self.assertEqual(response.status_code, 404)

    def test_edit_page_displays_delete_option(self):
        note = self.create_note(title="Training decision")

        response = self.client.get(reverse("notes:update", args=[note.pk]))

        self.assertContains(response, reverse("notes:delete", args=[note.pk]))
        self.assertContains(response, "Delete note")
        self.assertContains(response, 'class="context-navigation"')

    def test_delete_confirmation_displays_note_details(self):
        note = self.create_note(title="Remove this reminder")

        response = self.client.get(reverse("notes:delete", args=[note.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, note.title)
        self.assertTrue(Note.objects.filter(pk=note.pk).exists())

    def test_user_can_delete_own_note_with_post(self):
        note = self.create_note(title="Obsolete reminder")

        response = self.client.post(reverse("notes:delete", args=[note.pk]))

        self.assertRedirects(response, reverse("notes:list"))
        self.assertFalse(Note.objects.filter(pk=note.pk).exists())

    def test_user_cannot_delete_another_users_note(self):
        note = self.create_note(title="Private note", owner=self.other_user)

        response = self.client.post(reverse("notes:delete", args=[note.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Note.objects.filter(pk=note.pk).exists())

    def test_notes_workspace_can_be_displayed_in_spanish(self):
        self.client.post(
            reverse("set_language"),
            {"language": "es", "next": reverse("notes:list")},
        )

        response = self.client.get(reverse("notes:list"))

        self.assertContains(response, "Conocimiento y decisiones")
        self.assertContains(response, "Área de notas")
        self.assertContains(response, "Añadir nota")
        self.assertContains(response, "Buscar")
        self.assertContains(response, "Todas las categorías")

        form_response = self.client.get(reverse("notes:create"))
        self.assertContains(form_response, "Volver a las notas")
