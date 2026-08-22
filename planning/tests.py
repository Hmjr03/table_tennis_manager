from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from planning.forms import CalendarEventForm
from planning.models import CalendarEvent


User = get_user_model()


class CalendarEventFormTests(TestCase):
    def setUp(self):
        self.start_datetime = timezone.now().replace(
            second=0,
            microsecond=0,
        )

    def build_form_data(self, **overrides):
        data = {
            "title": "Training session",
            "description": "Technical training",
            "event_type": CalendarEvent.EventType.TRAINING,
            "start_datetime": self.start_datetime.strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "end_datetime": (
                self.start_datetime + timedelta(hours=2)
            ).strftime("%Y-%m-%dT%H:%M"),
            "location": "Main training hall",
            "priority": CalendarEvent.Priority.MEDIUM,
        }

        data.update(overrides)

        return data

    def test_valid_event_form(self):
        form = CalendarEventForm(
            data=self.build_form_data()
        )

        self.assertTrue(form.is_valid())

    def test_title_must_have_at_least_three_characters(self):
        form = CalendarEventForm(
            data=self.build_form_data(
                title="AB",
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Event title must contain at least 3 characters.",
            form.errors["title"],
        )

    def test_end_datetime_must_be_after_start_datetime(self):
        form = CalendarEventForm(
            data=self.build_form_data(
                end_datetime=self.start_datetime.strftime(
                    "%Y-%m-%dT%H:%M"
                ),
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            "The end date and time must be after "
            "the start date and time.",
            form.non_field_errors(),
        )

    def test_event_can_have_optional_description_and_location(self):
        form = CalendarEventForm(
            data=self.build_form_data(
                description="",
                location="",
            )
        )

        self.assertTrue(form.is_valid())


class CalendarEventModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="planner",
            email="planner@example.com",
            password="StrongPassword123!",
            role=User.Role.COACH,
        )

    def test_event_belongs_to_owner(self):
        event = CalendarEvent.objects.create(
            owner=self.user,
            title="Competition",
            event_type=CalendarEvent.EventType.COMPETITION,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(hours=3),
        )

        self.assertEqual(event.owner, self.user)

    def test_event_string_representation(self):
        event = CalendarEvent.objects.create(
            owner=self.user,
            title="Annual planning",
            event_type=CalendarEvent.EventType.OTHER,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(hours=1),
        )

        self.assertEqual(
            str(event),
            "Annual planning",
        )

from django.urls import reverse


class CalendarViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="calendar_user",
            email="calendar@example.com",
            password="StrongPassword123!",
            role=User.Role.COACH,
        )

        self.other_user = User.objects.create_user(
            username="other_user",
            email="other@example.com",
            password="StrongPassword123!",
            role=User.Role.ATHLETE,
        )

        self.client.force_login(self.user)

    def test_calendar_requires_authentication(self):
        self.client.logout()

        response = self.client.get(
            reverse("planning:calendar")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_calendar_page_loads(self):
        response = self.client.get(
            reverse("planning:calendar")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "planning/calendar.html",
        )

    def test_calendar_displays_user_events(self):
        start_datetime = timezone.now().replace(
            hour=10,
            minute=0,
            second=0,
            microsecond=0,
        )

        CalendarEvent.objects.create(
            owner=self.user,
            title="Technical training",
            event_type=CalendarEvent.EventType.TRAINING,
            start_datetime=start_datetime,
            end_datetime=start_datetime + timedelta(hours=2),
        )

        response = self.client.get(
            reverse("planning:calendar"),
            {
                "year": start_datetime.year,
                "month": start_datetime.month,
            },
        )

        self.assertContains(
            response,
            "Technical training",
        )

    def test_calendar_does_not_display_other_users_events(self):
        start_datetime = timezone.now().replace(
            hour=14,
            minute=0,
            second=0,
            microsecond=0,
        )

        CalendarEvent.objects.create(
            owner=self.other_user,
            title="Private training",
            event_type=CalendarEvent.EventType.TRAINING,
            start_datetime=start_datetime,
            end_datetime=start_datetime + timedelta(hours=1),
        )

        response = self.client.get(
            reverse("planning:calendar"),
            {
                "year": start_datetime.year,
                "month": start_datetime.month,
            },
        )

        self.assertNotContains(
            response,
            "Private training",
        )

    def test_calendar_can_navigate_to_requested_month(self):
        response = self.client.get(
            reverse("planning:calendar"),
            {
                "year": 2027,
                "month": 7,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context["year"],
            2027,
        )

        self.assertEqual(
            response.context["current_month"].month,
            7,
        )

    def test_calendar_handles_invalid_month(self):
        response = self.client.get(
            reverse("planning:calendar"),
            {
                "year": "invalid",
                "month": "invalid",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

