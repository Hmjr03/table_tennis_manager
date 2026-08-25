from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = "INCOME", _("Income")
        EXPENSE = "EXPENSE", _("Expense")

    class Area(models.TextChoices):
        PERSONAL = "PERSONAL", _("Personal")
        PROFESSIONAL = "PROFESSIONAL", _("Professional")

    class Category(models.TextChoices):
        HOUSING = "HOUSING", _("Housing")
        FOOD = "FOOD", _("Food")
        TRANSPORT = "TRANSPORT", _("Transport")
        HEALTH = "HEALTH", _("Health")
        EDUCATION = "EDUCATION", _("Education")
        LEISURE = "LEISURE", _("Leisure")
        SUBSCRIPTIONS = "SUBSCRIPTIONS", _("Subscriptions")
        TAXES = "TAXES", _("Taxes")
        TOURNAMENT_FEES = "TOURNAMENT_FEES", _("Tournament fees")
        TRAINING = "TRAINING", _("Training")
        COACHING = "COACHING", _("Coaching")
        TRAVEL = "TRAVEL", _("Travel")
        HOTEL = "HOTEL", _("Hotel")
        EQUIPMENT = "EQUIPMENT", _("Equipment")
        CLUB_FEES = "CLUB_FEES", _("Club fees")
        FEDERATION_FEES = "FEDERATION_FEES", _("Federation fees")
        RECOVERY = "RECOVERY", _("Medical / recovery")
        MARKETING = "MARKETING", _("Marketing")
        COURSES = "COURSES", _("Courses")
        SPONSORSHIP = "SPONSORSHIP", _("Sponsorship")
        PRIZE_MONEY = "PRIZE_MONEY", _("Prize money")
        SALARY = "SALARY", _("Salary")
        OTHER = "OTHER", _("Other")

    class PaymentMethod(models.TextChoices):
        CASH = "CASH", _("Cash")
        DEBIT_CARD = "DEBIT_CARD", _("Debit card")
        CREDIT_CARD = "CREDIT_CARD", _("Credit card")
        BANK_TRANSFER = "BANK_TRANSFER", _("Bank transfer")
        DIGITAL_WALLET = "DIGITAL_WALLET", _("Digital wallet")
        OTHER = "OTHER", _("Other")

    class Status(models.TextChoices):
        PAID = "PAID", _("Paid")
        PENDING = "PENDING", _("Pending")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    competition_record = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
    )
    area = models.CharField(max_length=15, choices=Area.choices)
    category = models.CharField(max_length=30, choices=Category.choices)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    date = models.DateField()
    description = models.CharField(max_length=255)
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.BANK_TRANSFER,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PAID,
    )
    is_recurring = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return self.description

    def clean(self):
        if (
            self.competition_record_id
            and self.owner_id
            and self.competition_record.owner_id != self.owner_id
        ):
            raise ValidationError(
                {
                    "competition_record": _(
                        "The selected competition does not belong to this account."
                    )
                }
            )
