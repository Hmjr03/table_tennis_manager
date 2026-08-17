from django import forms

from matches.models import Match
from players.models import Player


class MatchForm(forms.ModelForm):
    played_at = forms.DateTimeField(
        input_formats=[
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M",
        ],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
            },
        ),
    )

    class Meta:
        model = Match
        fields = (
            "player",
            "opponent_name",
            "competition",
            "played_at",
            "best_of",
            "status",
            "player_sets_won",
            "opponent_sets_won",
            "notes",
        )

        widgets = {
            "opponent_name": forms.TextInput(
                attrs={
                    "placeholder": "Opponent's name",
                }
            ),
            "competition": forms.TextInput(
                attrs={
                    "placeholder": "Tournament, league, club...",
                }
            ),
            "player_sets_won": forms.NumberInput(
                attrs={
                    "min": 0,
                    "placeholder": "0",
                }
            ),
            "opponent_sets_won": forms.NumberInput(
                attrs={
                    "min": 0,
                    "placeholder": "0",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": (
                        "Tactics, observations, key moments..."
                    ),
                }
            ),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.owner = owner

        if owner is not None:
            self.fields["player"].queryset = Player.objects.filter(
                user=owner
            ).order_by(
                "last_name",
                "first_name",
            )

        self.fields["player"].label = "Player"
        self.fields["opponent_name"].label = "Opponent"
        self.fields["competition"].label = "Competition / Event"
        self.fields["played_at"].label = "Date and time"
        self.fields["best_of"].label = "Match format"
        self.fields["status"].label = "Status"
        self.fields["player_sets_won"].label = "Player sets won"
        self.fields["opponent_sets_won"].label = "Opponent sets won"
        self.fields["notes"].label = "Match notes"

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get("status")
        player_sets = cleaned_data.get("player_sets_won")
        opponent_sets = cleaned_data.get("opponent_sets_won")

        if status == Match.Status.COMPLETED:
            if player_sets is None or opponent_sets is None:
                self.add_error(
                    "player_sets_won",
                    "Enter both scores for a completed match.",
                )

        else:
            if player_sets is not None or opponent_sets is not None:
                self.add_error(
                    "player_sets_won",
                    "Remove the score because the match is not completed.",
                )

        return cleaned_data
