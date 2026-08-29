from django import forms
from django.utils.translation import gettext_lazy as _

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
                "step": 60,
            },
        ),
    )

    class Meta:
        model = Match
        fields = (
            "player",
            "opponent_name",
            "competition_record",
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
                    "placeholder": _("Opponent's name"),
                }
            ),
            "competition": forms.TextInput(
                attrs={
                    "placeholder": _("Tournament, league, club..."),
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
                        _("Tactics, observations, key moments...")
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
            self.fields["competition_record"].queryset = (
                owner.competitions.all().order_by("start_date", "name")
            )
        else:
            self.fields["competition_record"].queryset = (
                self.fields["competition_record"].queryset.none()
            )

        self.fields["player"].empty_label = _("Select player")
        self.fields["competition_record"].empty_label = _(
            "No linked competition"
        )

        self.fields["player"].label = _("Player")
        self.fields["opponent_name"].label = _("Opponent")
        self.fields["competition_record"].label = _("Registered competition")
        self.fields["competition"].label = _("Competition name (optional)")
        self.fields["played_at"].label = _("Date and time")
        self.fields["best_of"].label = _("Match format")
        self.fields["status"].label = _("Status")
        self.fields["player_sets_won"].label = _("Player sets won")
        self.fields["opponent_sets_won"].label = _("Opponent sets won")
        self.fields["notes"].label = _("Match notes")

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get("status")
        player_sets = cleaned_data.get("player_sets_won")
        opponent_sets = cleaned_data.get("opponent_sets_won")
        competition_record = cleaned_data.get("competition_record")

        if competition_record is not None:
            cleaned_data["competition"] = competition_record.name

        if status == Match.Status.COMPLETED:
            if player_sets is None or opponent_sets is None:
                self.add_error(
                    "player_sets_won",
                    _("Enter both scores for a completed match."),
                )

        else:
            if player_sets is not None or opponent_sets is not None:
                self.add_error(
                    "player_sets_won",
                    _("Remove the score because the match is not completed."),
                )

        return cleaned_data
