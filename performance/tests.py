from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from matches.models import Match
from players.models import Player


User = get_user_model()


class PerformanceDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="performance-user",
            email="performance@example.com",
            password="StrongPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="other-user",
            email="other@example.com",
            password="StrongPassword123!",
        )

        self.player = Player.objects.create(
            user=self.user,
            first_name="John",
            last_name="Player",
            hand=Player.Hand.RIGHT,
        )

        self.other_player = Player.objects.create(
            user=self.other_user,
            first_name="Other",
            last_name="Player",
            hand=Player.Hand.LEFT,
        )

        self.client.login(
            username="performance-user",
            password="StrongPassword123!",
        )

    def create_match(
        self,
        *,
        player,
        opponent_name,
        player_sets,
        opponent_sets,
        competition="Test Tournament",
        days_ago=0,
        owner=None,
    ):
        owner = owner or player.user

        return Match.objects.create(
            owner=owner,
            player=player,
            opponent_name=opponent_name,
            competition=competition,
            played_at=timezone.now() - timedelta(
                days=days_ago,
            ),
            best_of=Match.BestOf.FIVE,
            status=Match.Status.COMPLETED,
            player_sets_won=player_sets,
            opponent_sets_won=opponent_sets,
        )

    def test_dashboard_requires_authentication(self):
        self.client.logout()

        response = self.client.get(
            reverse("performance:dashboard")
        )

        self.assertRedirects(
            response,
            (
                reverse("accounts:login")
                + "?next="
                + reverse("performance:dashboard")
            ),
        )

    def test_analysis_is_available_inside_matches_section(self):
        response = self.client.get(reverse("matches:analysis"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "matches/match_analysis.html")
        self.assertContains(response, reverse("matches:list"))
        self.assertContains(response, "Performance analysis")

    def test_main_navigation_has_no_standalone_performance_link(self):
        response = self.client.get(reverse("matches:list"))

        self.assertNotContains(response, 'href="/performance/"')
        self.assertContains(response, reverse("matches:analysis"))

    def test_dashboard_calculates_match_statistics(self):
        self.create_match(
            player=self.player,
            opponent_name="Opponent One",
            player_sets=3,
            opponent_sets=1,
            days_ago=3,
        )

        self.create_match(
            player=self.player,
            opponent_name="Opponent Two",
            player_sets=2,
            opponent_sets=3,
            days_ago=2,
        )

        self.create_match(
            player=self.player,
            opponent_name="Opponent Three",
            player_sets=3,
            opponent_sets=0,
            days_ago=1,
        )

        response = self.client.get(
            reverse("performance:dashboard")
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["total_matches"],
            3,
        )

        self.assertEqual(
            response.context["wins"],
            2,
        )

        self.assertEqual(
            response.context["losses"],
            1,
        )

        self.assertEqual(
            response.context["win_rate"],
            66.7,
        )

        self.assertEqual(
            response.context["sets_won"],
            8,
        )

        self.assertEqual(
            response.context["sets_lost"],
            4,
        )

        self.assertEqual(
            response.context["sets_difference"],
            4,
        )

    def test_dashboard_only_uses_completed_matches(self):
        self.create_match(
            player=self.player,
            opponent_name="Completed",
            player_sets=3,
            opponent_sets=1,
        )

        Match.objects.create(
            owner=self.user,
            player=self.player,
            opponent_name="Scheduled",
            competition="Future Tournament",
            played_at=timezone.now() + timedelta(days=2),
            best_of=Match.BestOf.FIVE,
            status=Match.Status.SCHEDULED,
        )

        response = self.client.get(
            reverse("performance:dashboard")
        )

        self.assertEqual(
            response.context["total_matches"],
            1,
        )

    def test_dashboard_can_filter_by_player(self):
        second_player = Player.objects.create(
            user=self.user,
            first_name="Second",
            last_name="Player",
            hand=Player.Hand.RIGHT,
        )

        self.create_match(
            player=self.player,
            opponent_name="First Opponent",
            player_sets=3,
            opponent_sets=0,
        )

        self.create_match(
            player=second_player,
            opponent_name="Second Opponent",
            player_sets=0,
            opponent_sets=3,
        )

        response = self.client.get(
            reverse("performance:dashboard"),
            {"player": second_player.pk},
        )

        self.assertEqual(
            response.context["total_matches"],
            1,
        )

        self.assertEqual(
            response.context["wins"],
            0,
        )

        self.assertEqual(
            response.context["losses"],
            1,
        )

    def test_dashboard_does_not_include_other_users_matches(self):
        self.create_match(
            player=self.player,
            opponent_name="My Opponent",
            player_sets=3,
            opponent_sets=1,
        )

        self.create_match(
            player=self.other_player,
            opponent_name="Other Opponent",
            player_sets=3,
            opponent_sets=0,
        )

        response = self.client.get(
            reverse("performance:dashboard")
        )

        self.assertEqual(
            response.context["total_matches"],
            1,
        )

    def test_dashboard_calculates_recent_form(self):
        for days_ago, player_sets, opponent_sets in [
            (5, 3, 1),
            (4, 3, 0),
            (3, 2, 3),
            (2, 3, 2),
            (1, 3, 1),
        ]:
            self.create_match(
                player=self.player,
                opponent_name=f"Opponent {days_ago}",
                player_sets=player_sets,
                opponent_sets=opponent_sets,
                days_ago=days_ago,
            )

        response = self.client.get(
            reverse("performance:dashboard")
        )

        self.assertEqual(
            response.context["recent_wins"],
            4,
        )

        self.assertEqual(
            response.context["recent_losses"],
            1,
        )

        self.assertEqual(
            response.context["recent_win_rate"],
            80.0,
        )

        self.assertEqual(
            response.context["form"],
            ["W", "W", "L", "W", "W"],
        )

    def test_dashboard_calculates_winning_streak(self):
        for days_ago, player_sets, opponent_sets in [
            (5, 3, 1),
            (4, 3, 0),
            (3, 3, 1),
            (2, 3, 2),
            (1, 3, 0),
        ]:
            self.create_match(
                player=self.player,
                opponent_name=f"Opponent {days_ago}",
                player_sets=player_sets,
                opponent_sets=opponent_sets,
                days_ago=days_ago,
            )

        response = self.client.get(
            reverse("performance:dashboard")
        )

        self.assertEqual(
            response.context["longest_win_streak"],
            5,
        )

        self.assertEqual(
            response.context["current_streak"],
            5,
        )

        self.assertEqual(
            response.context["current_streak_type"],
            "Win",
        )

    def test_dashboard_displays_empty_state_without_matches(self):
        response = self.client.get(
            reverse("performance:dashboard")
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["total_matches"],
            0,
        )

        self.assertContains(
            response,
            "Your performance story starts with your first match.",
        )
