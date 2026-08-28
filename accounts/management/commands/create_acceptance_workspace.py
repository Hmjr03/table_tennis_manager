from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from competitions.models import Competition
from finances.models import Transaction
from matches.models import Match
from notes.models import Note
from planning.models import CalendarEvent
from players.models import Player


DEMO_USERNAME = "acceptance-demo"
DEMO_EMAIL = "acceptance-demo@example.test"
DEMO_PASSWORD = "TableTennisDemo2026!"


class Command(BaseCommand):
    help = "Create an isolated local workspace for release acceptance testing."

    def handle(self, *args, **options):
        database = settings.DATABASES["default"]
        database_name = Path(str(database.get("NAME", ""))).name
        if not settings.DEBUG or database["ENGINE"] != "django.db.backends.sqlite3":
            raise CommandError("Acceptance data is allowed only in local debug mode.")
        if not database_name.startswith("ttm_acceptance"):
            raise CommandError(
                "Use an isolated database whose filename starts with "
                "'ttm_acceptance'."
            )

        User = get_user_model()
        if User.objects.filter(username=DEMO_USERNAME).exists():
            self.stdout.write(self.style.SUCCESS("Acceptance workspace is ready."))
            self._print_access()
            return

        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        today = timezone.localdate()
        user = User.objects.create_user(
            username=DEMO_USERNAME,
            email=DEMO_EMAIL,
            password=DEMO_PASSWORD,
            first_name="Demo",
            last_name="Manager",
            role=User.Role.COACH,
            is_active=True,
            terms_accepted_at=now,
            privacy_notice_acknowledged_at=now,
            legal_documents_version=settings.LEGAL_DOCUMENTS_VERSION,
            onboarding_dismissed_at=now,
        )
        player = Player.objects.create(
            user=user,
            first_name="Alex",
            last_name="Rossi",
            hand=Player.Hand.RIGHT,
            national_ranking=42,
            world_ranking=380,
        )
        competition = Competition.objects.create(
            owner=user,
            name="European Table Tennis Cup",
            competition_type=Competition.CompetitionType.CUP,
            status=Competition.Status.PLANNED,
            start_date=today + timedelta(days=18),
            end_date=today + timedelta(days=20),
            location="Milan",
            season=str(today.year),
        )
        competition.players.add(player)
        Match.objects.create(
            owner=user,
            player=player,
            opponent_name="Marco Silva",
            competition="Regional League",
            played_at=now - timedelta(days=7),
            best_of=Match.BestOf.FIVE,
            status=Match.Status.COMPLETED,
            player_sets_won=3,
            opponent_sets_won=1,
            notes="Strong receive and controlled first attack.",
        )
        CalendarEvent.objects.create(
            owner=user,
            title="Technical training",
            description="Serve, receive and third-ball practice.",
            event_type=CalendarEvent.EventType.TRAINING,
            start_datetime=now + timedelta(days=1, hours=2),
            end_datetime=now + timedelta(days=1, hours=4),
            location="Main Sports Hall",
            priority=CalendarEvent.Priority.HIGH,
        )
        Transaction.objects.create(
            owner=user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            area=Transaction.Area.PROFESSIONAL,
            category=Transaction.Category.EQUIPMENT,
            amount=Decimal("89.90"),
            date=today,
            description="Competition equipment",
            payment_method=Transaction.PaymentMethod.CREDIT_CARD,
            status=Transaction.Status.PAID,
        )
        Note.objects.create(
            owner=user,
            competition_record=competition,
            title="Competition preparation",
            content="Review short receive patterns and travel checklist.",
            category=Note.Category.COMPETITION,
            is_pinned=True,
        )

        self.stdout.write(self.style.SUCCESS("Acceptance workspace created."))
        self._print_access()

    def _print_access(self):
        self.stdout.write(f"Username: {DEMO_USERNAME}")
        self.stdout.write(f"Password: {DEMO_PASSWORD}")
