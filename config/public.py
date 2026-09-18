from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext as _

PUBLIC_PAGES = ('home', 'subscriptions:plans', 'legal:privacy', 'legal:terms')
ORIGIN = 'https://escolatmmanager.com'


def public_metadata(request):
    name = request.resolver_match.view_name if request.resolver_match else ''
    indexable = name in PUBLIC_PAGES
    return {
        'seo_indexable': indexable,
        'seo_canonical': ORIGIN + request.path if indexable else '',
        'seo_description': _(
            'Organize matches, training, competitions and finances. Try ETM Manager for 30 days without a card.'
        ) if name == 'home' else _('ETM Manager - Track players, matches and performance.'),
    }


def robots(request):
    return HttpResponse(
        'User-agent: *\nDisallow: /admin/\nSitemap: ' + ORIGIN + '/sitemap.xml\n',
        content_type='text/plain',
    )


def sitemap(request):
    urls = ''.join('<url><loc>' + ORIGIN + reverse(name) + '</loc></url>' for name in PUBLIC_PAGES)
    return HttpResponse('<?xml version="1.0" encoding="UTF-8"?>'
                        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                        + urls + '</urlset>', content_type='application/xml')
