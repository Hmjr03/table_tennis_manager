from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from matches.models import Match
from players.forms import PlayerForm

from players.models import Player


User = get_user_model()


class PlayerTestMixin:
    def create_user(
        self,
        username="player-manager",
        email="manager@example.com",
    ):
        return User.objects.create_user(
            username=username,
            email=email,
            password="StrongPassword123!",
            role="CLUB",
        )

    def create_player(
        self,
        user,
        first_name="John",
        last_name="Smith",
        ranking=25,
    ):
        return Player.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date(1995, 5, 15),
            hand=Player.Hand.RIGHT,
            national_ranking=ranking,
        )


class PlayerModelTests(PlayerTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user()

    def test_player_string_representation(self):
        player = self.create_player(
            self.user,
            first_name="John",
            last_name="Smith",
        )

        self.assertEqual(
            str(player),
            "John Smith",
        )

    def test_player_belongs_to_user(self):
        player = self.create_player(self.user)

        self.assertEqual(
            player.user,
            self.user,
        )

    def test_player_default_rankings_are_zero(self):
        player = Player.objects.create(
            user=self.user,
            first_name="Maria",
            last_name="Silva",
            hand=Player.Hand.LEFT,
        )

        self.assertEqual(
            player.national_ranking,
            0,
        )
        self.assertEqual(player.world_ranking, 0)

    def test_player_default_hand_is_right(self):
        player = Player.objects.create(
            user=self.user,
            first_name="Maria",
            last_name="Silva",
        )

        self.assertEqual(
            player.hand,
            Player.Hand.RIGHT,
        )

    def test_players_are_ordered_by_last_name_and_first_name(self):
        self.create_player(
            self.user,
            first_name="Carlos",
            last_name="Zeta",
        )

        self.create_player(
            self.user,
            first_name="Ana",
            last_name="Alves",
        )

        self.create_player(
            self.user,
            first_name="Bruno",
            last_name="Alves",
        )

        players = list(Player.objects.all())

        self.assertEqual(
            players[0].first_name,
            "Ana",
        )

        self.assertEqual(
            players[1].first_name,
            "Bruno",
        )

        self.assertEqual(
            players[2].first_name,
            "Carlos",
        )


class PlayerFormDateTests(TestCase):
    def test_date_of_birth_cannot_be_in_the_future(self):
        form = PlayerForm(
            data={
                "first_name": "Maria",
                "last_name": "Silva",
                "date_of_birth": (
                    timezone.localdate() + timedelta(days=1)
                ).isoformat(),
                "hand": Player.Hand.RIGHT,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("date_of_birth", form.errors)


class PlayerListViewTests(PlayerTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user()

        self.other_user = self.create_user(
            username="other-manager",
            email="other@example.com",
        )

        self.url = reverse("players:list")

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            "/accounts/login/",
            response.url,
        )

    def test_authenticated_user_can_access_player_list(self):
        self.client.login(
            username="player-manager",
            password="StrongPassword123!",
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "players/player_list.html",
        )

    def test_player_list_contains_only_current_users_players(self):
        self.create_player(
            self.user,
            first_name="John",
            last_name="Smith",
        )

        self.create_player(
            self.other_user,
            first_name="Other",
            last_name="Player",
        )

        self.client.login(
            username="player-manager",
            password="StrongPassword123!",
        )

        response = self.client.get(self.url)

        self.assertContains(
            response,
            "John",
        )

        self.assertNotContains(
            response,
            "Other",
        )

        self.assertEqual(response.context["total_players"], 1)
        self.assertEqual(response.context["ranked_players"], 1)
        self.assertEqual(response.context["profiles_to_complete"], 0)

    def test_player_list_identifies_profiles_to_complete(self):
        Player.objects.create(
            user=self.user,
            first_name="Maria",
            last_name="Silva",
            hand=Player.Hand.LEFT,
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.context["profiles_to_complete"], 1)
        self.assertContains(response, "Profiles to complete")
        self.assertContains(response, "Not ranked")

    def test_player_list_can_be_displayed_in_spanish(self):
        self.create_player(self.user)
        self.client.force_login(self.user)
        self.client.post(
            reverse("set_language"),
            {"language": "es", "next": self.url},
        )

        response = self.client.get(self.url)

        self.assertContains(response, "Gestión de atletas")
        self.assertContains(response, "Total de jugadores")
        self.assertContains(response, "Añadir jugador")
        self.assertContains(response, "Perfiles por completar")


class PlayerCreateViewTests(PlayerTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user()

        self.url = reverse("players:create")

        self.client.login(
            username="player-manager",
            password="StrongPassword123!",
        )

    def test_player_create_page_loads(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "players/player_form.html",
        )
        self.assertContains(response, 'class="context-navigation"')
        self.assertContains(response, reverse("players:list"))

    def test_authenticated_user_can_create_player(self):
        response = self.client.post(
            self.url,
            {
                "first_name": "Maria",
                "last_name": "Silva",
                "date_of_birth": "1998-07-20",
                "hand": Player.Hand.LEFT,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        player = Player.objects.get(
            first_name="Maria",
            last_name="Silva",
        )

        self.assertEqual(
            player.user,
            self.user,
        )

        self.assertRedirects(
            response,
            reverse(
                "players:detail",
                kwargs={"pk": player.pk},
            ),
        )

    def test_invalid_first_name_does_not_create_player(self):
        response = self.client.post(
            self.url,
            {
                "first_name": "A",
                "last_name": "Silva",
                "date_of_birth": "1998-07-20",
                "hand": Player.Hand.RIGHT,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            Player.objects.count(),
            0,
        )

        self.assertContains(
            response,
            _("First name must contain at least 2 characters."),
        )

    def test_invalid_last_name_does_not_create_player(self):
        response = self.client.post(
            self.url,
            {
                "first_name": "Maria",
                "last_name": "S",
                "date_of_birth": "1998-07-20",
                "hand": Player.Hand.RIGHT,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            Player.objects.count(),
            0,
        )

        self.assertContains(
            response,
            _("Last name must contain at least 2 characters."),
        )


class PlayerDetailViewTests(PlayerTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user()

        self.other_user = self.create_user(
            username="other-manager",
            email="other@example.com",
        )

        self.player = self.create_player(
            self.user,
            first_name="John",
            last_name="Smith",
        )

        self.other_player = self.create_player(
            self.other_user,
            first_name="Other",
            last_name="Player",
        )

        self.client.login(
            username="player-manager",
            password="StrongPassword123!",
        )

    def test_player_detail_page_loads(self):
        response = self.client.get(
            reverse(
                "players:detail",
                kwargs={"pk": self.player.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "players/player_detail.html",
        )

        self.assertContains(
            response,
            "John",
        )

        self.assertContains(
            response,
            "Smith",
        )

    def test_user_cannot_access_another_users_player(self):
        response = self.client.get(
            reverse(
                "players:detail",
                kwargs={"pk": self.other_player.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_player_detail_can_be_displayed_in_spanish(self):
        self.client.post(
            reverse("set_language"),
            {
                "language": "es",
                "next": reverse("players:detail", args=[self.player.pk]),
            },
        )

        response = self.client.get(
            reverse("players:detail", args=[self.player.pk])
        )

        self.assertContains(response, "Ranking mundial")
        self.assertContains(response, "Partidos jugados")
        self.assertContains(response, "Estadísticas por liga")
        self.assertContains(response, "Porcentaje de victorias")

    def test_detail_calculates_overall_and_league_statistics(self):
        for competition, player_score, opponent_score in (
            ("Italian League", 3, 1),
            ("Italian League", 2, 3),
            ("French League", 3, 0),
        ):
            Match.objects.create(
                owner=self.user,
                player=self.player,
                opponent_name="League opponent",
                competition=competition,
                played_at=timezone.now(),
                best_of=Match.BestOf.FIVE,
                status=Match.Status.COMPLETED,
                player_sets_won=player_score,
                opponent_sets_won=opponent_score,
            )
        Match.objects.create(
            owner=self.user,
            player=self.player,
            opponent_name="Future opponent",
            competition="Italian League",
            played_at=timezone.now(),
            status=Match.Status.SCHEDULED,
        )

        response = self.client.get(
            reverse("players:detail", kwargs={"pk": self.player.pk})
        )

        self.assertEqual(response.context["total_matches"], 3)
        self.assertEqual(response.context["wins"], 2)
        self.assertEqual(response.context["losses"], 1)
        self.assertEqual(response.context["win_rate"], 66.7)
        italian = next(
            row for row in response.context["league_stats"]
            if row["name"] == "Italian League"
        )
        self.assertEqual(italian["matches_played"], 2)
        self.assertEqual(italian["wins"], 1)
        self.assertEqual(italian["losses"], 1)
        self.assertEqual(italian["win_rate"], 50.0)
        self.assertContains(response, "Statistics by league")


class PlayerUpdateViewTests(PlayerTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user()

        self.other_user = self.create_user(
            username="other-manager",
            email="other@example.com",
        )

        self.player = self.create_player(
            self.user,
            first_name="John",
            last_name="Smith",
        )

        self.other_player = self.create_player(
            self.other_user,
            first_name="Other",
            last_name="Player",
        )

        self.client.login(
            username="player-manager",
            password="StrongPassword123!",
        )

    def test_user_can_update_own_player(self):
        response = self.client.post(
            reverse(
                "players:edit",
                kwargs={"pk": self.player.pk},
            ),
            {
                "first_name": "Jonathan",
                "last_name": "Smith",
                "date_of_birth": "1995-05-15",
                "hand": Player.Hand.LEFT,
                "world_ranking": "145",
                "national_ranking": "12",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "players:detail",
                kwargs={"pk": self.player.pk},
            ),
        )

        self.player.refresh_from_db()

        self.assertEqual(
            self.player.first_name,
            "Jonathan",
        )

        self.assertEqual(
            self.player.hand,
            Player.Hand.LEFT,
        )
        self.assertEqual(self.player.world_ranking, 145)
        self.assertEqual(self.player.national_ranking, 12)

    def test_user_cannot_update_another_users_player(self):
        response = self.client.get(
            reverse(
                "players:edit",
                kwargs={"pk": self.other_player.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class PlayerDeleteViewTests(PlayerTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user()

        self.other_user = self.create_user(
            username="other-manager",
            email="other@example.com",
        )

        self.player = self.create_player(
            self.user,
            first_name="John",
            last_name="Smith",
        )

        self.other_player = self.create_player(
            self.other_user,
            first_name="Other",
            last_name="Player",
        )

        self.client.login(
            username="player-manager",
            password="StrongPassword123!",
        )

    def test_delete_confirmation_page_loads(self):
        response = self.client.get(
            reverse(
                "players:delete",
                kwargs={"pk": self.player.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "players/player_confirm_delete.html",
        )

    def test_user_can_delete_own_player(self):
        response = self.client.post(
            reverse(
                "players:delete",
                kwargs={"pk": self.player.pk},
            )
        )

        self.assertRedirects(
            response,
            reverse("players:list"),
        )

        self.assertFalse(
            Player.objects.filter(
                pk=self.player.pk
            ).exists()
        )

    def test_user_cannot_delete_another_users_player(self):
        response = self.client.post(
            reverse(
                "players:delete",
                kwargs={"pk": self.other_player.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertTrue(
            Player.objects.filter(
                pk=self.other_player.pk
            ).exists()
        )
