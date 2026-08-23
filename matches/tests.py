from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from matches.forms import MatchForm
from matches.models import Match
from players.models import Player


User = get_user_model()


class MatchTestMixin:
    password = "StrongPassword123!"

    def create_user(
        self,
        username="match-manager",
        email="match-manager@example.com",
    ):
        return User.objects.create_user(
            username=username,
            email=email,
            password=self.password,
            role=User.Role.COACH,
        )

    def create_player(
        self,
        user,
        first_name="John",
        last_name="Smith",
    ):
        return Player.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
        )

    def create_match(
        self,
        owner,
        player,
        opponent_name="Opponent",
        status=Match.Status.SCHEDULED,
        player_sets_won=None,
        opponent_sets_won=None,
    ):
        return Match.objects.create(
            owner=owner,
            player=player,
            opponent_name=opponent_name,
            competition="Test competition",
            played_at=timezone.now(),
            best_of=Match.BestOf.FIVE,
            status=status,
            player_sets_won=player_sets_won,
            opponent_sets_won=opponent_sets_won,
        )

    def build_form_data(
        self,
        player,
        **overrides,
    ):
        data = {
            "player": player.pk,
            "opponent_name": "Test Opponent",
            "competition": "Test Competition",
            "played_at": (
                timezone.now() + timedelta(days=1)
            ).strftime("%Y-%m-%dT%H:%M"),
            "best_of": Match.BestOf.FIVE,
            "status": Match.Status.SCHEDULED,
            "player_sets_won": "",
            "opponent_sets_won": "",
            "notes": "Test notes",
        }

        data.update(overrides)

        return data


class MatchModelTests(MatchTestMixin, TestCase):
    def setUp(self):
        self.user = self.create_user()
        self.player = self.create_player(self.user)

    def test_match_belongs_to_owner(self):
        match = self.create_match(
            self.user,
            self.player,
        )

        self.assertEqual(match.owner, self.user)

    def test_match_string_representation(self):
        match = self.create_match(
            self.user,
            self.player,
            opponent_name="Robert",
        )

        self.assertIn("John Smith vs Robert", str(match))

    def test_completed_match_result_is_win(self):
        match = self.create_match(
            self.user,
            self.player,
            status=Match.Status.COMPLETED,
            player_sets_won=3,
            opponent_sets_won=1,
        )

        self.assertEqual(match.result, "Win")
        self.assertEqual(match.score, "3 - 1")

    def test_completed_match_result_is_loss(self):
        match = self.create_match(
            self.user,
            self.player,
            status=Match.Status.COMPLETED,
            player_sets_won=1,
            opponent_sets_won=3,
        )

        self.assertEqual(match.result, "Loss")
        self.assertEqual(match.score, "1 - 3")

    def test_match_rejects_player_from_another_account(self):
        other_user = self.create_user(
            username="other-manager",
            email="other-manager@example.com",
        )
        other_player = self.create_player(
            other_user,
            first_name="Other",
            last_name="Player",
        )

        match = Match(
            owner=self.user,
            player=other_player,
            opponent_name="Opponent",
            played_at=timezone.now(),
            best_of=Match.BestOf.FIVE,
            status=Match.Status.SCHEDULED,
        )

        with self.assertRaises(ValidationError):
            match.full_clean()


class MatchFormSecurityTests(MatchTestMixin, TestCase):
    def setUp(self):
        self.user = self.create_user()
        self.other_user = self.create_user(
            username="other-manager",
            email="other@example.com",
        )

        self.player = self.create_player(
            self.user,
            first_name="Own",
            last_name="Player",
        )

        self.other_player = self.create_player(
            self.other_user,
            first_name="Private",
            last_name="Player",
        )

    def test_form_only_exposes_players_owned_by_current_user(self):
        form = MatchForm(owner=self.user)

        queryset = form.fields["player"].queryset

        self.assertIn(self.player, queryset)
        self.assertNotIn(self.other_player, queryset)

    def test_form_rejects_player_from_another_account(self):
        form = MatchForm(
            data=self.build_form_data(self.other_player),
            owner=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("player", form.errors)


class MatchListViewTests(MatchTestMixin, TestCase):
    def setUp(self):
        self.user = self.create_user()
        self.other_user = self.create_user(
            username="other-manager",
            email="other@example.com",
        )

        self.player = self.create_player(
            self.user,
            first_name="Own",
            last_name="Player",
        )

        self.other_player = self.create_player(
            self.other_user,
            first_name="Other",
            last_name="Player",
        )

        self.own_match = self.create_match(
            self.user,
            self.player,
            opponent_name="Visible Opponent",
        )

        self.other_match = self.create_match(
            self.other_user,
            self.other_player,
            opponent_name="Private Opponent",
        )

        self.url = reverse("matches:list")

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_list_contains_only_current_users_matches(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visible Opponent")
        self.assertNotContains(response, "Private Opponent")

    def test_player_filter_cannot_expose_another_users_match(self):
        self.client.force_login(self.user)

        response = self.client.get(
            self.url,
            {
                "player": str(self.other_player.pk),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Private Opponent")


class MatchDetailSecurityTests(MatchTestMixin, TestCase):
    def setUp(self):
        self.user = self.create_user()
        self.other_user = self.create_user(
            username="other-manager",
            email="other@example.com",
        )

        self.player = self.create_player(self.user)

        self.other_player = self.create_player(
            self.other_user,
            first_name="Other",
            last_name="Player",
        )

        self.own_match = self.create_match(
            self.user,
            self.player,
        )

        self.other_match = self.create_match(
            self.other_user,
            self.other_player,
            opponent_name="Private Opponent",
        )

        self.client.force_login(self.user)

    def test_user_can_access_own_match(self):
        response = self.client.get(
            reverse(
                "matches:detail",
                kwargs={"pk": self.own_match.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_user_cannot_access_another_users_match(self):
        response = self.client.get(
            reverse(
                "matches:detail",
                kwargs={"pk": self.other_match.pk},
            )
        )

        self.assertEqual(response.status_code, 404)


class MatchCreateSecurityTests(MatchTestMixin, TestCase):
    def setUp(self):
        self.user = self.create_user()
        self.other_user = self.create_user(
            username="other-manager",
            email="other@example.com",
        )

        self.player = self.create_player(self.user)

        self.other_player = self.create_player(
            self.other_user,
            first_name="Other",
            last_name="Player",
        )

        self.client.force_login(self.user)

    def test_user_can_create_match_for_own_player(self):
        response = self.client.post(
            reverse("matches:create"),
            self.build_form_data(self.player),
        )

        self.assertEqual(response.status_code, 302)

        match = Match.objects.get(
            owner=self.user,
            opponent_name="Test Opponent",
        )

        self.assertEqual(match.player, self.player)

    def test_user_cannot_create_match_for_another_users_player(self):
        response = self.client.post(
            reverse("matches:create"),
            self.build_form_data(self.other_player),
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Match.objects.filter(
                owner=self.user,
                player=self.other_player,
            ).exists()
        )


class MatchUpdateSecurityTests(MatchTestMixin, TestCase):
    def setUp(self):
        self.user = self.create_user()
        self.other_user = self.create_user(
            username="other-manager",
            email="other@example.com",
        )

        self.player = self.create_player(self.user)

        self.other_player = self.create_player(
            self.other_user,
            first_name="Other",
            last_name="Player",
        )

        self.own_match = self.create_match(
            self.user,
            self.player,
        )

        self.other_match = self.create_match(
            self.other_user,
            self.other_player,
            opponent_name="Private Opponent",
        )

        self.client.force_login(self.user)

    def test_user_can_update_own_match(self):
        response = self.client.post(
            reverse(
                "matches:update",
                kwargs={"pk": self.own_match.pk},
            ),
            self.build_form_data(
                self.player,
                opponent_name="Updated Opponent",
            ),
        )

        self.assertEqual(response.status_code, 302)

        self.own_match.refresh_from_db()

        self.assertEqual(
            self.own_match.opponent_name,
            "Updated Opponent",
        )

    def test_user_cannot_open_update_for_another_users_match(self):
        response = self.client.get(
            reverse(
                "matches:update",
                kwargs={"pk": self.other_match.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_post_update_to_another_users_match(self):
        response = self.client.post(
            reverse(
                "matches:update",
                kwargs={"pk": self.other_match.pk},
            ),
            self.build_form_data(
                self.player,
                opponent_name="Hacked Opponent",
            ),
        )

        self.assertEqual(response.status_code, 404)

        self.other_match.refresh_from_db()

        self.assertEqual(
            self.other_match.opponent_name,
            "Private Opponent",
        )


class MatchDeleteSecurityTests(MatchTestMixin, TestCase):
    def setUp(self):
        self.user = self.create_user()
        self.other_user = self.create_user(
            username="other-manager",
            email="other@example.com",
        )

        self.player = self.create_player(self.user)

        self.other_player = self.create_player(
            self.other_user,
            first_name="Other",
            last_name="Player",
        )

        self.own_match = self.create_match(
            self.user,
            self.player,
        )

        self.other_match = self.create_match(
            self.other_user,
            self.other_player,
        )

        self.client.force_login(self.user)

    def test_user_can_delete_own_match(self):
        response = self.client.post(
            reverse(
                "matches:delete",
                kwargs={"pk": self.own_match.pk},
            )
        )

        self.assertRedirects(
            response,
            reverse("matches:list"),
        )

        self.assertFalse(
            Match.objects.filter(
                pk=self.own_match.pk,
            ).exists()
        )

    def test_user_cannot_open_delete_page_for_another_users_match(self):
        response = self.client.get(
            reverse(
                "matches:delete",
                kwargs={"pk": self.other_match.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_another_users_match(self):
        response = self.client.post(
            reverse(
                "matches:delete",
                kwargs={"pk": self.other_match.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            Match.objects.filter(
                pk=self.other_match.pk,
            ).exists()
        )
