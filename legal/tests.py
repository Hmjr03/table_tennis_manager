from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class LegalPageTests(TestCase):
    def test_privacy_policy_is_public(self):
        response = self.client.get(reverse("legal:privacy"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "legal/privacy_policy.html")
        self.assertContains(response, "Privacy Policy")

    def test_terms_of_use_are_public(self):
        response = self.client.get(reverse("legal:terms"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "legal/terms_of_use.html")
        self.assertContains(response, "Terms of Use")

    def test_legal_pages_are_localized(self):
        expectations = {
            "pt-br": (
                "Política de Privacidade",
                "Termos de Uso",
            ),
            "es": (
                "Política de Privacidad",
                "Términos de Uso",
            ),
        }

        for language, texts in expectations.items():
            with self.subTest(language=language):
                self.client.cookies[
                    settings.LANGUAGE_COOKIE_NAME
                ] = language
                privacy_response = self.client.get(
                    reverse("legal:privacy")
                )
                terms_response = self.client.get(
                    reverse("legal:terms")
                )
                self.assertContains(privacy_response, texts[0])
                self.assertContains(terms_response, texts[1])
