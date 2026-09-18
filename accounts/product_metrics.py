from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import render
from matches.models import Match
from planning.models import CalendarEvent


def product_metrics(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    # Only self-service registrations with consent; exclude staff/demo accounts.
    users = get_user_model().objects.filter(
        terms_accepted_at__isnull=False, is_staff=False,
    ).exclude(email__iendswith='.invalid')
    active = users.filter(is_active=True)
    engaged = active.annotate(
        has_match=Exists(Match.objects.filter(owner_id=OuterRef('pk'))),
        has_event=Exists(CalendarEvent.objects.filter(owner_id=OuterRef('pk'))),
    ).filter(Q(has_match=True) | Q(has_event=True))
    registered, activated, started = users.count(), active.count(), engaged.count()
    return render(request, 'admin/product_metrics.html', {
        'title': 'Adoção do ETM Manager',
        'registered': registered, 'activated': activated, 'started': started,
        'activation_rate': round(100 * activated / registered, 1) if registered else 0,
        'usage_rate': round(100 * started / activated, 1) if activated else 0,
        'has_permission': True, 'site_header': 'Administração ETM Manager',
    })
