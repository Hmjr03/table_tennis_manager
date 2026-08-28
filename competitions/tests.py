from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from competitions.forms import CompetitionForm
from competitions.models import Competition
from matches.models import Match
from finances.models import Transaction
from notes.models import Note
from planning.models import CalendarEvent
from players.models import Player


User = get_user_model()


class CompetitionTestMixin:
    def create_user(self, username="competition-owner"):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="StrongPassword123!",
        )

    def create_competition(self, owner, name="Italian Open"):
        return Competition.objects.create(
            owner=owner,
            name=name,
            competition_type=Competition.CompetitionType.TOURNAMENT,
            start_date=date(2026, 9, 20),
            location="Milan",
            season="2026/27",
        )


class CompetitionModelAndFormTests(CompetitionTestMixin, TestCase):
    def test_end_date_cannot_precede_start_date(self):
        owner = self.create_user()
        form = CompetitionForm(
            {
                "name": "Italian Open",
                "competition_type": Competition.CompetitionType.TOURNAMENT,
                "status": Competition.Status.PLANNED,
                "start_date": "2026-09-20",
                "end_date": "2026-09-19",
            },
            owner=owner,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("end_date", form.errors)

    def test_form_only_offers_players_owned_by_current_user(self):
        owner = self.create_user()
        other = self.create_user("other-competition-owner")
        own_player = Player.objects.create(
            user=owner,
            first_name="Ana",
            last_name="Silva",
        )
        other_player = Player.objects.create(
            user=other,
            first_name="Other",
            last_name="Player",
        )

        form = CompetitionForm(owner=owner)

        self.assertIn(own_player, form.fields["players"].queryset)
        self.assertNotIn(other_player, form.fields["players"].queryset)


class CompetitionViewTests(CompetitionTestMixin, TestCase):
    def setUp(self):
        self.owner = self.create_user()
        self.other = self.create_user("other-owner")
        self.client.force_login(self.owner)

    def test_list_only_displays_current_users_competitions(self):
        own = self.create_competition(self.owner)
        other = self.create_competition(self.other, "Private Competition")

        response = self.client.get(reverse("competitions:list"))

        self.assertContains(response, own.name)
        self.assertNotContains(response, other.name)

    def test_competition_list_distinguishes_first_use_and_empty_search(self):
        response = self.client.get(reverse("competitions:list"))
        self.assertContains(response, "Add your first competition")

        self.create_competition(self.owner)
        response = self.client.get(reverse("competitions:list"), {"q": "missing"})
        self.assertContains(response, "No competitions match these filters")
        self.assertContains(response, "Clear filters")

    def test_user_can_create_competition_with_own_player(self):
        player = Player.objects.create(
            user=self.owner,
            first_name="Humberto",
            last_name="Junior",
        )
        response = self.client.post(
            reverse("competitions:create"),
            {
                "name": "French League",
                "competition_type": Competition.CompetitionType.LEAGUE,
                "status": Competition.Status.ACTIVE,
                "start_date": "2026-08-24",
                "location": "Paris",
                "season": "2026/27",
                "players": [player.pk],
            },
        )

        competition = Competition.objects.get(name="French League")
        self.assertRedirects(
            response,
            reverse("competitions:detail", kwargs={"pk": competition.pk}),
        )
        self.assertEqual(competition.owner, self.owner)
        self.assertIn(player, competition.players.all())
        synced_event = CalendarEvent.objects.get(
            competition_record=competition,
            is_competition_sync=True,
        )
        self.assertEqual(synced_event.owner, self.owner)
        self.assertEqual(synced_event.title, competition.name)
        self.assertEqual(synced_event.location, competition.location)
        self.assertEqual(
            synced_event.event_type,
            CalendarEvent.EventType.COMPETITION,
        )

    def test_editing_competition_updates_only_its_synced_event(self):
        competition = self.create_competition(self.owner)
        manual_event = CalendarEvent.objects.create(
            owner=self.owner,
            competition_record=competition,
            title="Manual travel briefing",
            event_type=CalendarEvent.EventType.MEETING,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(hours=1),
        )

        response = self.client.post(
            reverse("competitions:update", args=[competition.pk]),
            {
                "name": "Italian Open Updated",
                "competition_type": Competition.CompetitionType.CHAMPIONSHIP,
                "status": Competition.Status.ACTIVE,
                "start_date": "2026-10-10",
                "end_date": "2026-10-12",
                "location": "Turin",
                "season": "2026/27",
            },
        )

        self.assertEqual(response.status_code, 302)
        synced_events = CalendarEvent.objects.filter(
            competition_record=competition,
            is_competition_sync=True,
        )
        self.assertEqual(synced_events.count(), 1)
        synced_event = synced_events.get()
        self.assertEqual(synced_event.title, "Italian Open Updated")
        self.assertEqual(synced_event.location, "Turin")
        self.assertEqual(
            timezone.localtime(synced_event.start_datetime).date(),
            date(2026, 10, 10),
        )
        self.assertEqual(
            timezone.localtime(synced_event.end_datetime).date(),
            date(2026, 10, 12),
        )
        manual_event.refresh_from_db()
        self.assertEqual(manual_event.title, "Manual travel briefing")

    def test_deleting_competition_preserves_synchronized_calendar_event(self):
        competition = self.create_competition(self.owner)
        self.client.post(
            reverse("competitions:update", args=[competition.pk]),
            {
                "name": competition.name,
                "competition_type": competition.competition_type,
                "status": competition.status,
                "start_date": competition.start_date.isoformat(),
            },
        )
        synced_event = CalendarEvent.objects.get(
            competition_record=competition,
            is_competition_sync=True,
        )

        self.client.post(reverse("competitions:delete", args=[competition.pk]))

        synced_event.refresh_from_db()
        self.assertIsNone(synced_event.competition_record)
        self.assertTrue(synced_event.is_competition_sync)

    def test_user_cannot_view_another_users_competition(self):
        competition = self.create_competition(self.other)

        response = self.client.get(
            reverse("competitions:detail", kwargs={"pk": competition.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_detail_calculates_linked_match_performance(self):
        competition = self.create_competition(self.owner)
        player = Player.objects.create(
            user=self.owner,
            first_name="Ana",
            last_name="Silva",
        )
        Match.objects.create(
            owner=self.owner,
            player=player,
            opponent_name="Opponent",
            competition=competition.name,
            competition_record=competition,
            played_at=timezone.now(),
            status=Match.Status.COMPLETED,
            player_sets_won=3,
            opponent_sets_won=1,
        )

        response = self.client.get(
            reverse("competitions:detail", kwargs={"pk": competition.pk})
        )

        self.assertEqual(response.context["total_matches"], 1)
        self.assertEqual(response.context["wins"], 1)
        self.assertEqual(response.context["win_rate"], 100.0)

    def test_deleting_competition_preserves_linked_records(self):
        competition = self.create_competition(self.owner)
        player = Player.objects.create(
            user=self.owner,
            first_name="Ana",
            last_name="Silva",
        )
        match = Match.objects.create(
            owner=self.owner,
            player=player,
            opponent_name="Opponent",
            competition=competition.name,
            competition_record=competition,
            played_at=timezone.now(),
        )
        event = CalendarEvent.objects.create(
            owner=self.owner,
            title=competition.name,
            competition_record=competition,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(hours=2),
        )

        self.client.post(
            reverse("competitions:delete", kwargs={"pk": competition.pk})
        )

        match.refresh_from_db()
        event.refresh_from_db()
        self.assertIsNone(match.competition_record)
        self.assertIsNone(event.competition_record)

    def test_linked_competition_prefills_new_match_and_event(self):
        competition = self.create_competition(self.owner)

        match_response = self.client.get(
            reverse("matches:create"),
            {"competition": competition.pk},
        )
        event_response = self.client.get(
            reverse("planning:create"),
            {"competition": competition.pk},
        )

        self.assertEqual(
            match_response.context["form"].initial["competition_record"],
            competition,
        )
        self.assertEqual(
            event_response.context["form"].initial["competition_record"],
            competition,
        )
        self.assertEqual(event_response.context["form"].initial["title"], competition.name)

    def test_competition_center_is_translated_in_portuguese_and_spanish(self):
        self.client.post(
            reverse("set_language"),
            {"language": "pt-br", "next": reverse("competitions:list")},
        )
        portuguese_response = self.client.get(reverse("competitions:list"))
        self.assertContains(portuguese_response, "Central de competições")
        self.assertContains(portuguese_response, "Adicionar competição")

        self.client.post(
            reverse("set_language"),
            {"language": "es", "next": reverse("competitions:list")},
        )
        spanish_response = self.client.get(reverse("competitions:list"))
        self.assertContains(spanish_response, "Centro de competiciones")
        self.assertContains(spanish_response, "Añadir competición")

    def test_invalid_competition_shortcut_is_ignored_safely(self):
        match_response = self.client.get(
            reverse("matches:create"),
            {"competition": "invalid"},
        )
        event_response = self.client.get(
            reverse("planning:create"),
            {"competition": "invalid"},
        )

        self.assertEqual(match_response.status_code, 200)
        self.assertEqual(event_response.status_code, 200)

    def test_competition_center_summarizes_finances_and_notes(self):
        competition = self.create_competition(self.owner)
        Transaction.objects.create(
            owner=self.owner,
            competition_record=competition,
            transaction_type=Transaction.TransactionType.INCOME,
            area=Transaction.Area.PROFESSIONAL,
            category=Transaction.Category.PRIZE_MONEY,
            amount=Decimal("500.00"),
            date=competition.start_date,
            description="Prize money",
        )
        Transaction.objects.create(
            owner=self.owner,
            competition_record=competition,
            transaction_type=Transaction.TransactionType.EXPENSE,
            area=Transaction.Area.PROFESSIONAL,
            category=Transaction.Category.TOURNAMENT_FEES,
            amount=Decimal("125.00"),
            date=competition.start_date,
            description="Entry fee",
        )
        Note.objects.create(
            owner=self.owner,
            competition_record=competition,
            title="Tactical preparation",
            content="Review serve receive patterns.",
            category=Note.Category.COMPETITION,
        )

        response = self.client.get(
            reverse("competitions:detail", kwargs={"pk": competition.pk})
        )

        self.assertEqual(response.context["competition_income"], Decimal("500.00"))
        self.assertEqual(response.context["competition_expenses"], Decimal("125.00"))
        self.assertEqual(response.context["competition_balance"], Decimal("375.00"))
        self.assertContains(response, "Tactical preparation")

    def test_finance_and_note_shortcuts_prefill_competition(self):
        competition = self.create_competition(self.owner)

        finance_response = self.client.get(
            reverse("finances:create"),
            {"competition": competition.pk},
        )
        note_response = self.client.get(
            reverse("notes:create"),
            {"competition": competition.pk},
        )

        self.assertEqual(
            finance_response.context["form"].initial["competition_record"],
            competition,
        )
        self.assertEqual(
            note_response.context["form"].initial["competition_record"],
            competition,
        )

    def test_deleting_competition_preserves_finances_and_notes(self):
        competition = self.create_competition(self.owner)
        transaction = Transaction.objects.create(
            owner=self.owner,
            competition_record=competition,
            transaction_type=Transaction.TransactionType.EXPENSE,
            area=Transaction.Area.PROFESSIONAL,
            category=Transaction.Category.OTHER,
            amount=Decimal("10.00"),
            date=competition.start_date,
            description="Preserved expense",
        )
        note = Note.objects.create(
            owner=self.owner,
            competition_record=competition,
            title="Preserved note",
            content="This note must remain available.",
        )

        self.client.post(
            reverse("competitions:delete", kwargs={"pk": competition.pk})
        )

        transaction.refresh_from_db()
        note.refresh_from_db()
        self.assertIsNone(transaction.competition_record)
        self.assertIsNone(note.competition_record)
