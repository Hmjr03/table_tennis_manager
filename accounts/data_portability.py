from django.utils import timezone


def iso(value):
    return value.isoformat() if value is not None else None


def export_user_data(user):
    players = list(user.players.all().order_by("id"))
    competitions = list(
        user.competitions.prefetch_related("players").order_by("id")
    )

    return {
        "format_version": "1.0",
        "generated_at": timezone.now().isoformat(),
        "account": {
            "id": user.pk,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_active": user.is_active,
            "date_joined": iso(user.date_joined),
            "last_login": iso(user.last_login),
            "terms_accepted_at": iso(user.terms_accepted_at),
            "privacy_notice_acknowledged_at": iso(
                user.privacy_notice_acknowledged_at
            ),
            "legal_documents_version": user.legal_documents_version,
        },
        "players": [
            {
                "id": player.pk,
                "first_name": player.first_name,
                "last_name": player.last_name,
                "date_of_birth": iso(player.date_of_birth),
                "hand": player.hand,
                "national_ranking": player.national_ranking,
                "world_ranking": player.world_ranking,
                "created_at": iso(player.created_at),
            }
            for player in players
        ],
        "competitions": [
            {
                "id": competition.pk,
                "name": competition.name,
                "competition_type": competition.competition_type,
                "status": competition.status,
                "start_date": iso(competition.start_date),
                "end_date": iso(competition.end_date),
                "location": competition.location,
                "season": competition.season,
                "notes": competition.notes,
                "player_ids": list(
                    competition.players.values_list("id", flat=True)
                ),
                "created_at": iso(competition.created_at),
                "updated_at": iso(competition.updated_at),
            }
            for competition in competitions
        ],
        "matches": [
            {
                "id": match.pk,
                "player_id": match.player_id,
                "opponent_name": match.opponent_name,
                "competition": match.competition,
                "competition_id": match.competition_record_id,
                "played_at": iso(match.played_at),
                "best_of": match.best_of,
                "status": match.status,
                "player_sets_won": match.player_sets_won,
                "opponent_sets_won": match.opponent_sets_won,
                "notes": match.notes,
                "created_at": iso(match.created_at),
                "updated_at": iso(match.updated_at),
            }
            for match in user.matches.all().order_by("id")
        ],
        "calendar_events": [
            {
                "id": event.pk,
                "title": event.title,
                "description": event.description,
                "event_type": event.event_type,
                "start_datetime": iso(event.start_datetime),
                "end_datetime": iso(event.end_datetime),
                "location": event.location,
                "priority": event.priority,
                "competition_id": event.competition_record_id,
                "created_at": iso(event.created_at),
                "updated_at": iso(event.updated_at),
            }
            for event in user.calendar_events.all().order_by("id")
        ],
        "transactions": [
            {
                "id": transaction.pk,
                "competition_id": transaction.competition_record_id,
                "transaction_type": transaction.transaction_type,
                "area": transaction.area,
                "category": transaction.category,
                "amount": str(transaction.amount),
                "date": iso(transaction.date),
                "description": transaction.description,
                "payment_method": transaction.payment_method,
                "status": transaction.status,
                "is_recurring": transaction.is_recurring,
                "notes": transaction.notes,
                "created_at": iso(transaction.created_at),
                "updated_at": iso(transaction.updated_at),
            }
            for transaction in user.transactions.all().order_by("id")
        ],
        "notes": [
            {
                "id": note.pk,
                "competition_id": note.competition_record_id,
                "title": note.title,
                "content": note.content,
                "category": note.category,
                "is_pinned": note.is_pinned,
                "is_archived": note.is_archived,
                "created_at": iso(note.created_at),
                "updated_at": iso(note.updated_at),
            }
            for note in user.notes.all().order_by("id")
        ],
    }
