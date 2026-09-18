from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override
from accounts.forms import UserRegistrationForm
from accounts.models import User


class PublicSiteTests(TestCase):
    def test_home_offer_support_and_demo_are_visible(self):
        with override('pt-br'):
            response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='pt-br')
            self.assertContains(response, 'Testar grátis por 30 dias')
            self.assertContains(response, 'dados fictícios de demonstração')
            self.assertContains(response, 'mailto:')
            self.assertContains(response, 'rel="canonical"')
            self.assertContains(response, 'property="og:image"')

    def test_signup_profile_is_localized(self):
        with override('pt-br'):
            html = UserRegistrationForm().as_p()
            self.assertIn('Seu perfil', html)
            self.assertIn('Treinador', html)
            self.assertNotIn('>Coach<', html)
        self.assertContains(self.client.get(reverse('accounts:register')), 'noindex, nofollow')

    def test_sitemap_only_contains_public_pages(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://escolatmmanager.com/plans/')
        self.assertNotContains(response, '/accounts/')
        self.assertNotContains(response, '/admin/')
        self.assertContains(self.client.get('/robots.txt'), 'Sitemap:')

    def test_metrics_require_owner_permission(self):
        self.assertEqual(self.client.get('/admin/product-metrics/').status_code, 302)
        user = User.objects.create_user(username='staff', is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get('/admin/product-metrics/').status_code, 403)
        user.is_superuser = True
        user.save()
        response = self.client.get('/admin/product-metrics/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['registered'], 0)
