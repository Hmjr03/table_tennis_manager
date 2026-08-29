from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override

from finances.forms import TransactionForm
from finances.models import Transaction


User = get_user_model()


class TransactionFormTests(TestCase):
    def form_data(self, **overrides):
        data = {
            "transaction_type": Transaction.TransactionType.EXPENSE,
            "area": Transaction.Area.PROFESSIONAL,
            "category": Transaction.Category.TOURNAMENT_FEES,
            "amount": "125.50",
            "date": timezone.localdate().isoformat(),
            "description": "National championship entry",
            "payment_method": Transaction.PaymentMethod.BANK_TRANSFER,
            "status": Transaction.Status.PAID,
            "notes": "",
        }
        data.update(overrides)
        return data

    def test_valid_transaction_form(self):
        self.assertTrue(TransactionForm(data=self.form_data()).is_valid())

    def test_amount_must_be_positive(self):
        form = TransactionForm(data=self.form_data(amount="0"))
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_amount_accepts_decimal_comma_for_portuguese_and_spanish(self):
        for language in ("pt-br", "es"):
            with self.subTest(language=language), override(language):
                form = TransactionForm(
                    data=self.form_data(amount="125,50")
                )
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data["amount"], Decimal("125.50"))

    def test_amount_uses_mobile_decimal_keyboard(self):
        field = TransactionForm().fields["amount"]

        self.assertEqual(field.widget.input_type, "text")
        self.assertEqual(field.widget.attrs["inputmode"], "decimal")

    def test_description_must_have_three_characters(self):
        form = TransactionForm(data=self.form_data(description="AB"))
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)

    def test_required_choice_prompts_are_translated(self):
        expected_prompts = {
            "pt-br": "Selecione o tipo de transação",
            "es": "Selecciona el tipo de transacción",
        }

        for language, expected in expected_prompts.items():
            with self.subTest(language=language), override(language):
                form = TransactionForm()
                prompt = form.fields["transaction_type"].choices[0][1]
                self.assertEqual(str(prompt), expected)


class TransactionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="finance_user",
            email="finance@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="other_finance_user",
            email="other-finance@example.com",
            password="StrongPassword123!",
        )
        self.client.force_login(self.user)

    def create_transaction(
        self,
        *,
        description,
        transaction_type,
        amount,
        owner=None,
        area=Transaction.Area.PROFESSIONAL,
        date=None,
    ):
        return Transaction.objects.create(
            owner=owner or self.user,
            transaction_type=transaction_type,
            area=area,
            category=Transaction.Category.OTHER,
            amount=amount,
            date=date or timezone.localdate(),
            description=description,
            payment_method=Transaction.PaymentMethod.BANK_TRANSFER,
            status=Transaction.Status.PAID,
        )

    def test_finance_page_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse("finances:list"))
        self.assertEqual(response.status_code, 302)

    def test_finance_page_guides_first_transaction(self):
        response = self.client.get(reverse("finances:list"))
        self.assertContains(response, "Build your financial overview")
        self.assertContains(response, "Add your first transaction")

    def test_empty_month_is_distinguished_from_first_use(self):
        self.create_transaction(
            description="Earlier expense",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("10.00"),
            date=timezone.localdate().replace(year=2020, month=1, day=10),
        )
        response = self.client.get(reverse("finances:list"))
        self.assertContains(response, "No transactions in this view")

    def test_month_summary_calculates_income_expenses_and_balance(self):
        self.create_transaction(
            description="Sponsorship",
            transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal("1000.00"),
        )
        self.create_transaction(
            description="Equipment",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("275.50"),
        )

        response = self.client.get(reverse("finances:list"))

        self.assertEqual(response.context["income"], Decimal("1000.00"))
        self.assertEqual(response.context["expenses"], Decimal("275.50"))
        self.assertEqual(response.context["balance"], Decimal("724.50"))

    def test_finance_page_does_not_expose_other_users_transactions(self):
        self.create_transaction(
            description="Visible expense",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("20.00"),
        )
        self.create_transaction(
            description="Private expense",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("900.00"),
            owner=self.other_user,
        )

        response = self.client.get(reverse("finances:list"))

        self.assertContains(response, "Visible expense")
        self.assertNotContains(response, "Private expense")
        self.assertEqual(response.context["expenses"], Decimal("20.00"))

    def test_area_filter_updates_table_and_summary(self):
        self.create_transaction(
            description="Professional travel",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("200.00"),
        )
        self.create_transaction(
            description="Personal dinner",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("50.00"),
            area=Transaction.Area.PERSONAL,
        )

        response = self.client.get(
            reverse("finances:list"),
            {"area": Transaction.Area.PERSONAL},
        )

        self.assertContains(response, "Personal dinner")
        self.assertNotContains(response, "Professional travel")
        self.assertEqual(response.context["expenses"], Decimal("50.00"))

    def test_create_transaction_assigns_authenticated_owner(self):
        response = self.client.post(
            reverse("finances:create"),
            {
                "transaction_type": Transaction.TransactionType.INCOME,
                "area": Transaction.Area.PROFESSIONAL,
                "category": Transaction.Category.SPONSORSHIP,
                "amount": "500.00",
                "date": timezone.localdate().isoformat(),
                "description": "Monthly sponsor payment",
                "payment_method": Transaction.PaymentMethod.BANK_TRANSFER,
                "status": Transaction.Status.PAID,
                "is_recurring": "on",
                "notes": "Contract payment",
            },
        )

        self.assertRedirects(response, reverse("finances:list"))
        transaction = Transaction.objects.get()
        self.assertEqual(transaction.owner, self.user)
        self.assertTrue(transaction.is_recurring)

    def test_transaction_form_uses_professional_context_navigation(self):
        response = self.client.get(reverse("finances:create"))

        self.assertContains(response, 'class="context-navigation"')
        self.assertContains(response, reverse("finances:list"))
        self.assertContains(response, "Back to finances")

    def test_user_cannot_edit_another_users_transaction(self):
        transaction = self.create_transaction(
            description="Other user record",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("80.00"),
            owner=self.other_user,
        )

        response = self.client.get(
            reverse("finances:update", args=[transaction.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_transactions_outside_selected_month_are_excluded(self):
        previous_month = timezone.localdate().replace(day=1) - timedelta(days=1)
        self.create_transaction(
            description="Older transaction",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("40.00"),
            date=previous_month,
        )

        response = self.client.get(reverse("finances:list"))

        self.assertNotContains(response, "Older transaction")
        self.assertEqual(response.context["expenses"], Decimal("0.00"))

    def test_finance_workspace_can_be_displayed_in_portuguese(self):
        self.client.post(
            reverse("set_language"),
            {"language": "pt-br", "next": reverse("finances:list")},
        )

        response = self.client.get(reverse("finances:list"))

        self.assertContains(response, "Gestão financeira")
        self.assertContains(response, "Área financeira")
        self.assertContains(response, "Construa sua visão financeira")
        self.assertContains(response, "Buscar")
        self.assertContains(response, "Todas as áreas")

        form_response = self.client.get(reverse("finances:create"))
        self.assertContains(form_response, "Voltar às finanças")
