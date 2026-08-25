from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from finances.models import Transaction
from notes.models import Note
from planning.models import CalendarEvent
from competitions.models import Competition


User = get_user_model()


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="humberto",
            first_name="Humberto",
            email="humberto@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPassword123!",
        )
        self.client.force_login(self.user)

    def create_event(
        self,
        *,
        title,
        event_type,
        starts_in,
        owner=None,
    ):
        start_datetime = timezone.now() + starts_in
        return CalendarEvent.objects.create(
            owner=owner or self.user,
            title=title,
            event_type=event_type,
            start_datetime=start_datetime,
            end_datetime=start_datetime + timedelta(hours=2),
            location="Main Sports Hall",
        )

    def test_dashboard_requires_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 302)

    def test_dashboard_displays_personalized_welcome(self):
        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Humberto")
        self.assertContains(response, "Your daily overview")

    def test_dashboard_selects_next_competition_and_counts_days(self):
        later_competition = self.create_event(
            title="International Open",
            event_type=CalendarEvent.EventType.COMPETITION,
            starts_in=timedelta(days=12),
        )
        next_competition = self.create_event(
            title="National Championship",
            event_type=CalendarEvent.EventType.COMPETITION,
            starts_in=timedelta(days=5),
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.context["next_competition"], next_competition)
        self.assertIn(response.context["days_until_competition"], {5, 6})
        self.assertContains(response, "National Championship")
        self.assertNotEqual(response.context["next_competition"], later_competition)

    def test_registered_competition_is_the_primary_dashboard_source(self):
        self.create_event(
            title="Legacy calendar tournament",
            event_type=CalendarEvent.EventType.COMPETITION,
            starts_in=timedelta(days=2),
        )
        competition = Competition.objects.create(
            owner=self.user,
            name="European Masters",
            start_date=timezone.localdate() + timedelta(days=7),
            location="Rome",
            status=Competition.Status.PLANNED,
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(
            response.context["next_competition_record"],
            competition,
        )
        self.assertEqual(response.context["days_until_competition"], 7)
        self.assertContains(response, "European Masters")
        self.assertContains(
            response,
            reverse("competitions:detail", args=[competition.pk]),
        )
        self.assertEqual(response.context["next_competition"].title, "Legacy calendar tournament")

    def test_dashboard_does_not_expose_other_users_registered_competition(self):
        Competition.objects.create(
            owner=self.other_user,
            name="Private tournament",
            start_date=timezone.localdate() + timedelta(days=3),
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertIsNone(response.context["next_competition_record"])
        self.assertNotContains(response, "Private tournament")

    def test_next_commitment_uses_only_professional_event_types(self):
        self.create_event(
            title="Sunday Tournament",
            event_type=CalendarEvent.EventType.COMPETITION,
            starts_in=timedelta(hours=2),
        )
        training = self.create_event(
            title="Technical training",
            event_type=CalendarEvent.EventType.TRAINING,
            starts_in=timedelta(hours=5),
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.context["next_commitment"], training)
        self.assertContains(response, "Technical training")

    def test_next_commitment_can_be_a_personal_event(self):
        personal_event = self.create_event(
            title="Family appointment",
            event_type=CalendarEvent.EventType.PERSONAL,
            starts_in=timedelta(hours=2),
        )
        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.context["next_commitment"], personal_event)
        self.assertContains(response, "Family appointment")

    def test_compact_calendar_displays_only_current_user_events(self):
        self.create_event(
            title="Visible recovery session",
            event_type=CalendarEvent.EventType.RECOVERY,
            starts_in=timedelta(hours=1),
        )
        self.create_event(
            title="Private meeting",
            event_type=CalendarEvent.EventType.MEETING,
            starts_in=timedelta(hours=1),
            owner=self.other_user,
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertContains(response, "Visible recovery session")
        self.assertNotContains(response, "Private meeting")
        self.assertContains(response, reverse("planning:calendar"))

    def test_dashboard_has_clear_empty_schedule_states(self):
        response = self.client.get(reverse("dashboard:home"))

        self.assertContains(response, "No competition scheduled")
        self.assertContains(response, "Your schedule is clear")
        self.assertContains(response, reverse("competitions:create"))

    def test_dashboard_does_not_display_recent_matches_section(self):
        response = self.client.get(reverse("dashboard:home"))

        self.assertNotContains(response, "Recent matches")
        self.assertNotIn("recent_matches", response.context)

    def test_dashboard_displays_current_month_financial_summary(self):
        Transaction.objects.create(
            owner=self.user,
            transaction_type=Transaction.TransactionType.INCOME,
            area=Transaction.Area.PROFESSIONAL,
            category=Transaction.Category.SPONSORSHIP,
            amount=Decimal("1200.00"),
            date=timezone.localdate(),
            description="Monthly sponsorship",
        )
        Transaction.objects.create(
            owner=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            area=Transaction.Area.PERSONAL,
            category=Transaction.Category.FOOD,
            amount=Decimal("150.00"),
            date=timezone.localdate(),
            description="Groceries",
        )
        Transaction.objects.create(
            owner=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            area=Transaction.Area.PROFESSIONAL,
            category=Transaction.Category.EQUIPMENT,
            amount=Decimal("200.00"),
            date=timezone.localdate(),
            description="New rubber",
            status=Transaction.Status.PENDING,
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.context["monthly_income"], Decimal("1200.00"))
        self.assertEqual(response.context["monthly_expenses"], Decimal("350.00"))
        self.assertEqual(response.context["monthly_balance"], Decimal("850.00"))
        self.assertEqual(response.context["personal_expenses"], Decimal("150.00"))
        self.assertEqual(response.context["professional_expenses"], Decimal("200.00"))
        self.assertEqual(response.context["pending_expenses"], Decimal("200.00"))
        self.assertContains(response, "Open finance workspace")

    def test_dashboard_financial_summary_does_not_include_other_user(self):
        Transaction.objects.create(
            owner=self.other_user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            area=Transaction.Area.PERSONAL,
            category=Transaction.Category.OTHER,
            amount=Decimal("999.00"),
            date=timezone.localdate(),
            description="Private transaction",
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.context["monthly_expenses"], Decimal("0.00"))
        self.assertNotContains(response, "Private transaction")

    def test_dashboard_displays_only_active_pinned_notes_for_user(self):
        visible_note = Note.objects.create(
            owner=self.user,
            title="Competition checklist",
            content="Confirm equipment and travel documents.",
            category=Note.Category.COMPETITION,
            is_pinned=True,
        )
        Note.objects.create(
            owner=self.user,
            title="Archived pinned note",
            content="Old information.",
            is_pinned=True,
            is_archived=True,
        )
        Note.objects.create(
            owner=self.other_user,
            title="Another user's pinned note",
            content="Private information.",
            is_pinned=True,
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertContains(response, visible_note.title)
        self.assertNotContains(response, "Archived pinned note")
        self.assertNotContains(response, "Another user's pinned note")
        self.assertContains(response, "Open notes workspace")
        self.assertContains(response, "Important notes")
        self.assertNotContains(response, "Pinned for attention")

    def test_user_can_switch_dashboard_to_portuguese(self):
        response = self.client.post(
            reverse("set_language"),
            {"language": "pt-br", "next": reverse("dashboard:home")},
            follow=True,
        )

        self.assertContains(response, "Sua visão geral diária")
        self.assertContains(response, "Próxima competição")
        self.assertContains(response, "Visão financeira")
        self.assertContains(response, "Notas importantes")

    def test_user_can_switch_dashboard_to_spanish(self):
        response = self.client.post(
            reverse("set_language"),
            {"language": "es", "next": reverse("dashboard:home")},
            follow=True,
        )

        self.assertContains(response, "Tu resumen diario")
        self.assertContains(response, "Próxima competición")
        self.assertContains(response, "Resumen financiero")
        self.assertContains(response, "Notas importantes")

    def test_compact_calendar_can_show_a_previous_month(self):
        past_event = self.create_event(
            title="Previous month review",
            event_type=CalendarEvent.EventType.MEETING,
            starts_in=timedelta(days=-40),
        )
        event_date = timezone.localtime(past_event.start_datetime).date()

        response = self.client.get(
            reverse("dashboard:home"),
            {"year": event_date.year, "month": event_date.month},
        )

        self.assertEqual(response.context["calendar_month"].year, event_date.year)
        self.assertEqual(response.context["calendar_month"].month, event_date.month)
        self.assertContains(response, "Previous month review")

    def test_compact_calendar_navigation_crosses_year_boundary(self):
        response = self.client.get(
            reverse("dashboard:home"),
            {"year": 2027, "month": 1},
        )

        self.assertEqual(
            response.context["previous_calendar_month"].isoformat(),
            "2026-12-01",
        )
        self.assertEqual(
            response.context["next_calendar_month"].isoformat(),
            "2027-02-01",
        )

    def test_compact_calendar_invalid_month_falls_back_to_current_month(self):
        response = self.client.get(
            reverse("dashboard:home"),
            {"year": "invalid", "month": "invalid"},
        )

        current_month = timezone.localdate().replace(day=1)
        self.assertEqual(response.context["calendar_month"], current_month)
