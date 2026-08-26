from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.utils.translation import gettext as _

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
            _("Event title must contain at least 3 characters."),
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
            _("The end date and time must be after "
              "the start date and time."),
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



class CalendarEventCreateFromDayTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="day_click_user",
            email="day-click@example.com",
            password="StrongPassword123!",
            role=User.Role.COACH,
        )

        self.client.force_login(self.user)

    def test_create_event_prefills_selected_calendar_date(self):
        response = self.client.get(
            reverse("planning:create"),
            {
                "date": "2026-08-23",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        form = response.context["form"]

        start_datetime = form.initial[
            "start_datetime"
        ]

        end_datetime = form.initial[
            "end_datetime"
        ]

        self.assertEqual(
            start_datetime.date().isoformat(),
            "2026-08-23",
        )

        self.assertEqual(
            start_datetime.hour,
            9,
        )

        self.assertEqual(
            end_datetime.date().isoformat(),
            "2026-08-23",
        )

        self.assertEqual(
            end_datetime.hour,
            10,
        )

    def test_create_event_uses_safe_defaults_for_invalid_selected_date(self):
        response = self.client.get(
            reverse("planning:create"),
            {
                "date": "invalid-date",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        form = response.context["form"]

        self.assertIn("start_datetime", form.initial)
        self.assertIn("end_datetime", form.initial)
        self.assertEqual(
            form.initial["end_datetime"] - form.initial["start_datetime"],
            timedelta(hours=1),
        )

    def test_create_event_uses_professional_context_navigation(self):
        response = self.client.get(reverse("planning:create"))

        self.assertContains(response, 'class="context-navigation"')
        self.assertContains(response, reverse("planning:calendar"))

    def test_calendar_can_be_displayed_in_portuguese(self):
        self.client.post(
            reverse("set_language"),
            {"language": "pt-br", "next": reverse("planning:calendar")},
        )

        response = self.client.get(reverse("planning:calendar"))

        self.assertContains(response, "Planejamento anual")
        self.assertContains(response, "Segunda")
        self.assertContains(response, "Adicionar evento")

    def test_event_form_can_be_displayed_in_spanish(self):
        self.client.post(
            reverse("set_language"),
            {"language": "es", "next": reverse("planning:create")},
        )

        response = self.client.get(reverse("planning:create"))

        self.assertContains(response, "Gestión del calendario")
        self.assertContains(response, "Información del evento")
        self.assertContains(response, "Fecha y hora de inicio")


class EventQuickUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="quick_editor",
            email="quick-editor@example.com",
            password="StrongPassword123!",
            role=User.Role.COACH,
        )
        self.other_user = User.objects.create_user(
            username="other_quick_editor",
            email="other-quick@example.com",
            password="StrongPassword123!",
            role=User.Role.COACH,
        )
        self.start = timezone.now().replace(second=0, microsecond=0)
        self.event = CalendarEvent.objects.create(
            owner=self.user,
            title="Italian League",
            description="Initial description",
            event_type=CalendarEvent.EventType.COMPETITION,
            start_datetime=self.start,
            end_datetime=self.start + timedelta(hours=2),
            location="Milano",
            priority=CalendarEvent.Priority.HIGH,
        )
        self.other_event = CalendarEvent.objects.create(
            owner=self.other_user,
            title="Private event",
            start_datetime=self.start,
            end_datetime=self.start + timedelta(hours=1),
        )
        self.client.force_login(self.user)

    def quick_update_url(self, event, section):
        return reverse("planning:quick_update", args=[event.pk, section])

    def test_detail_provides_independent_section_forms(self):
        response = self.client.get(
            reverse("planning:detail", args=[self.event.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("schedule_form", response.context)
        self.assertIn("classification_form", response.context)
        self.assertIn("description_form", response.context)
        self.assertContains(response, "Select a section below")

    def test_user_can_update_schedule_without_full_event_form(self):
        new_start = self.start + timedelta(days=1)
        response = self.client.post(
            self.quick_update_url(self.event, "schedule"),
            {
                "start_datetime": new_start.strftime("%Y-%m-%dT%H:%M"),
                "end_datetime": (new_start + timedelta(hours=3)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "location": "Roma",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith("#event-schedule"))
        self.event.refresh_from_db()
        self.assertEqual(self.event.location, "Roma")
        self.assertEqual(self.event.title, "Italian League")

    def test_invalid_schedule_returns_open_editor_and_preserves_event(self):
        response = self.client.post(
            self.quick_update_url(self.event, "schedule"),
            {
                "start_datetime": self.start.strftime("%Y-%m-%dT%H:%M"),
                "end_datetime": self.start.strftime("%Y-%m-%dT%H:%M"),
                "location": "Changed location",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.context["active_section"], "schedule")
        self.assertContains(response, "schedule-editor", status_code=400)
        self.event.refresh_from_db()
        self.assertEqual(self.event.location, "Milano")

    def test_user_can_update_classification(self):
        response = self.client.post(
            self.quick_update_url(self.event, "classification"),
            {
                "event_type": CalendarEvent.EventType.MEETING,
                "priority": CalendarEvent.Priority.LOW,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.event_type, CalendarEvent.EventType.MEETING)
        self.assertEqual(self.event.priority, CalendarEvent.Priority.LOW)

    def test_user_can_update_description(self):
        response = self.client.post(
            self.quick_update_url(self.event, "description"),
            {"description": "Updated tactical information"},
        )

        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.description, "Updated tactical information")

    def test_quick_update_requires_post_and_event_ownership(self):
        own_response = self.client.get(
            self.quick_update_url(self.event, "description")
        )
        other_response = self.client.post(
            self.quick_update_url(self.other_event, "description"),
            {"description": "Unauthorized change"},
        )

        self.assertEqual(own_response.status_code, 405)
        self.assertEqual(other_response.status_code, 404)
        self.other_event.refresh_from_db()
        self.assertEqual(self.other_event.description, "")
