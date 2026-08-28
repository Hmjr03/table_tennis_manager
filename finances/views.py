from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from finances.forms import TransactionForm
from finances.models import Transaction
from competitions.models import Competition


def _selected_month(value):
    today = timezone.localdate()
    if value:
        try:
            return date.fromisoformat(f"{value}-01")
        except ValueError:
            pass
    return today.replace(day=1)


def _total(queryset, transaction_type):
    return queryset.filter(
        transaction_type=transaction_type,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")


@login_required
def transaction_list(request):
    month = _selected_month(request.GET.get("month", "").strip())
    transactions = Transaction.objects.filter(
        owner=request.user,
        date__year=month.year,
        date__month=month.month,
    )

    area = request.GET.get("area", "").strip()
    transaction_type = request.GET.get("type", "").strip()
    status = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()
    total_transaction_count = Transaction.objects.filter(
        owner=request.user
    ).count()
    has_active_filters = bool(area or transaction_type or status or query)

    if area in Transaction.Area.values:
        transactions = transactions.filter(area=area)
    if transaction_type in Transaction.TransactionType.values:
        transactions = transactions.filter(transaction_type=transaction_type)
    if status in Transaction.Status.values:
        transactions = transactions.filter(status=status)
    if query:
        transactions = transactions.filter(
            Q(description__icontains=query)
            | Q(notes__icontains=query)
        )

    income = _total(transactions, Transaction.TransactionType.INCOME)
    expenses = _total(transactions, Transaction.TransactionType.EXPENSE)
    balance = income - expenses

    paginator = Paginator(transactions, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "finances/transaction_list.html",
        {
            "page_obj": page_obj,
            "income": income,
            "expenses": expenses,
            "balance": balance,
            "selected_month": month,
            "month_value": month.strftime("%Y-%m"),
            "area_choices": Transaction.Area.choices,
            "type_choices": Transaction.TransactionType.choices,
            "status_choices": Transaction.Status.choices,
            "current_area": area,
            "current_type": transaction_type,
            "current_status": status,
            "current_query": query,
            "total_transaction_count": total_transaction_count,
            "has_active_filters": has_active_filters,
        },
    )


@login_required
def transaction_create(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, owner=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.owner = request.user
            transaction.save()
            messages.success(request, _("Transaction created successfully."))
            return redirect("finances:list")
    else:
        competition_id = request.GET.get("competition", "").strip()
        selected_competition = None
        if competition_id.isdigit():
            selected_competition = Competition.objects.filter(
                owner=request.user,
                pk=competition_id,
            ).first()
        form = TransactionForm(
            owner=request.user,
            initial={
                "date": timezone.localdate(),
                "competition_record": selected_competition,
                "area": Transaction.Area.PROFESSIONAL,
            },
        )

    return render(
        request,
        "finances/transaction_form.html",
        {"form": form, "page_title": _("Add transaction"), "submit_label": _("Save transaction")},
    )


@login_required
def transaction_update(request, pk):
    transaction = get_object_or_404(
        Transaction,
        pk=pk,
        owner=request.user,
    )
    if request.method == "POST":
        form = TransactionForm(
            request.POST,
            instance=transaction,
            owner=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, _("Transaction updated successfully."))
            return redirect("finances:list")
    else:
        form = TransactionForm(instance=transaction, owner=request.user)

    return render(
        request,
        "finances/transaction_form.html",
        {"form": form, "page_title": _("Edit transaction"), "submit_label": _("Save changes"), "transaction": transaction},
    )


@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(
        Transaction,
        pk=pk,
        owner=request.user,
    )
    if request.method == "POST":
        transaction.delete()
        messages.success(request, _("Transaction deleted successfully."))
        return redirect("finances:list")

    return render(
        request,
        "finances/transaction_confirm_delete.html",
        {"transaction": transaction},
    )
