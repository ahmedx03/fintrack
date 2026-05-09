"""
Transaction, category, budget, recurring-transaction, CSV-export, and pagination tests.

Note on paginated responses
────────────────────────────
TransactionListCreateView uses CursorPagination, so GET /api/transactions/
returns  {"next": ..., "previous": ..., "results": [...]}  instead of a bare list.
All list assertions go through res.data["results"].
"""

import csv
import datetime
import io

import pytest
from rest_framework import status
from transactions.models import Budget, Category, RecurringTransaction, Transaction

CATEGORIES_URL   = "/api/categories/"
TRANSACTIONS_URL = "/api/transactions/"
EXPORT_URL       = "/api/transactions/export/"
BUDGETS_URL      = "/api/budgets/"
RECURRING_URL    = "/api/recurring/"


def cat_url(pk):      return f"/api/categories/{pk}/"
def tx_url(pk):       return f"/api/transactions/{pk}/"
def budget_url(pk):   return f"/api/budgets/{pk}/"
def recurring_url(pk): return f"/api/recurring/{pk}/"


# ─────────────────────────────────────────────────────────────────────────────────
# Category CRUD
# ─────────────────────────────────────────────────────────────────────────────────
class TestCategoryCreate:
    def test_create_expense_category(self, auth_client_a, user_a):
        res = auth_client_a.post(CATEGORIES_URL, {"name": "Rent", "type": "expense"})
        assert res.status_code == status.HTTP_201_CREATED
        assert Category.objects.filter(name="Rent", user=user_a).exists()

    def test_create_income_category(self, auth_client_a):
        res = auth_client_a.post(CATEGORIES_URL, {"name": "Freelance", "type": "income"})
        assert res.status_code == status.HTTP_201_CREATED

    def test_missing_type_rejected(self, auth_client_a):
        assert auth_client_a.post(CATEGORIES_URL, {"name": "Oops"}).status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_type_rejected(self, auth_client_a):
        assert auth_client_a.post(CATEGORIES_URL, {"name": "Misc", "type": "neither"}).status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_rejected(self, api_client, db):
        assert api_client.post(CATEGORIES_URL, {"name": "Rent", "type": "expense"}).status_code == status.HTTP_401_UNAUTHORIZED


class TestCategoryList:
    def test_lists_only_own_categories(self, auth_client_a, cat_a_expense, cat_b_expense):
        res = auth_client_a.get(CATEGORIES_URL)
        names = [c["name"] for c in res.data]
        assert "Food" in names
        assert "Travel" not in names

    def test_empty_list_when_no_categories(self, auth_client_a, db):
        assert auth_client_a.get(CATEGORIES_URL).data == []


class TestCategoryDelete:
    def test_delete_own_category(self, auth_client_a, cat_a_expense):
        res = auth_client_a.delete(cat_url(cat_a_expense.id))
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not Category.objects.filter(id=cat_a_expense.id).exists()

    def test_idor_cannot_delete_other_users_category(self, auth_client_a, cat_b_expense):
        res = auth_client_a.delete(cat_url(cat_b_expense.id))
        assert res.status_code == status.HTTP_404_NOT_FOUND
        assert Category.objects.filter(id=cat_b_expense.id).exists()

    def test_delete_nonexistent_returns_404(self, auth_client_a, db):
        assert auth_client_a.delete(cat_url(99999)).status_code == status.HTTP_404_NOT_FOUND


# ─────────────────────────────────────────────────────────────────────────────────
# Transaction CRUD + pagination
# ─────────────────────────────────────────────────────────────────────────────────
class TestTransactionCreate:
    def test_create_expense(self, auth_client_a, user_a, cat_a_expense):
        res = auth_client_a.post(TRANSACTIONS_URL, {
            "type": "expense", "amount": "25.00",
            "date": "2024-06-01", "category": cat_a_expense.id, "note": "coffee",
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert Transaction.objects.filter(user=user_a, note="coffee").exists()

    def test_create_income(self, auth_client_a, cat_a_income):
        res = auth_client_a.post(TRANSACTIONS_URL, {
            "type": "income", "amount": "3000.00", "date": "2024-06-01",
            "category": cat_a_income.id,
        })
        assert res.status_code == status.HTTP_201_CREATED

    def test_create_without_category_allowed(self, auth_client_a):
        res = auth_client_a.post(TRANSACTIONS_URL, {"type": "expense", "amount": "10.00", "date": "2024-06-01"})
        assert res.status_code == status.HTTP_201_CREATED

    def test_unauthenticated_rejected(self, api_client, db):
        assert api_client.post(TRANSACTIONS_URL, {"type": "expense", "amount": "10.00", "date": "2024-06-01"}).status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_amount_rejected(self, auth_client_a):
        assert auth_client_a.post(TRANSACTIONS_URL, {"type": "expense", "date": "2024-06-01"}).status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_date_rejected(self, auth_client_a):
        assert auth_client_a.post(TRANSACTIONS_URL, {"type": "expense", "amount": "10.00"}).status_code == status.HTTP_400_BAD_REQUEST


class TestTransactionList:
    def test_returns_paginated_shape(self, auth_client_a, tx_a):
        res = auth_client_a.get(TRANSACTIONS_URL)
        assert res.status_code == status.HTTP_200_OK
        assert "results" in res.data   # cursor pagination envelope
        assert "next"    in res.data

    def test_lists_only_own_transactions(self, auth_client_a, tx_a, tx_b):
        res = auth_client_a.get(TRANSACTIONS_URL)
        ids = [t["id"] for t in res.data["results"]]
        assert tx_a.id in ids
        assert tx_b.id not in ids

    def test_filter_by_type_expense(self, auth_client_a, user_a, cat_a_expense, cat_a_income):
        Transaction.objects.create(user=user_a, type="expense", amount="20.00",
                                   date=datetime.date.today(), category=cat_a_expense)
        Transaction.objects.create(user=user_a, type="income",  amount="500.00",
                                   date=datetime.date.today(), category=cat_a_income)
        res = auth_client_a.get(TRANSACTIONS_URL + "?type=expense")
        assert all(t["type"] == "expense" for t in res.data["results"])

    def test_filter_by_date_range(self, auth_client_a, user_a):
        Transaction.objects.create(user=user_a, type="expense", amount="10.00", date=datetime.date(2024, 3, 1))
        Transaction.objects.create(user=user_a, type="expense", amount="20.00", date=datetime.date(2024, 5, 15))
        Transaction.objects.create(user=user_a, type="expense", amount="30.00", date=datetime.date(2024, 7, 1))
        res = auth_client_a.get(TRANSACTIONS_URL + "?from=2024-04-01&to=2024-06-30")
        assert len(res.data["results"]) == 1
        assert float(res.data["results"][0]["amount"]) == 20.00

    def test_filter_by_category(self, auth_client_a, user_a, cat_a_expense, cat_a_income):
        Transaction.objects.create(user=user_a, type="expense", amount="10.00",
                                   date=datetime.date.today(), category=cat_a_expense)
        Transaction.objects.create(user=user_a, type="income",  amount="500.00",
                                   date=datetime.date.today(), category=cat_a_income)
        res = auth_client_a.get(TRANSACTIONS_URL + f"?category={cat_a_expense.id}")
        assert len(res.data["results"]) == 1

    def test_malformed_date_does_not_500(self, auth_client_a, db):
        res = auth_client_a.get(TRANSACTIONS_URL + "?from=not-a-date&to=also-bad")
        assert res.status_code == status.HTTP_200_OK

    def test_unauthenticated_rejected(self, api_client, db):
        assert api_client.get(TRANSACTIONS_URL).status_code == status.HTTP_401_UNAUTHORIZED


class TestTransactionRetrieve:
    def test_retrieve_own_transaction(self, auth_client_a, tx_a):
        res = auth_client_a.get(tx_url(tx_a.id))
        assert res.status_code == status.HTTP_200_OK and res.data["id"] == tx_a.id

    def test_idor_cannot_retrieve_other_users_transaction(self, auth_client_a, tx_b):
        assert auth_client_a.get(tx_url(tx_b.id)).status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_nonexistent_returns_404(self, auth_client_a, db):
        assert auth_client_a.get(tx_url(99999)).status_code == status.HTTP_404_NOT_FOUND


class TestTransactionUpdate:
    def test_patch_amount(self, auth_client_a, tx_a):
        auth_client_a.patch(tx_url(tx_a.id), {"amount": "75.00"})
        tx_a.refresh_from_db()
        assert float(tx_a.amount) == 75.00

    def test_patch_note(self, auth_client_a, tx_a):
        auth_client_a.patch(tx_url(tx_a.id), {"note": "dinner"})
        tx_a.refresh_from_db()
        assert tx_a.note == "dinner"

    def test_idor_cannot_patch_other_users_transaction(self, auth_client_a, tx_b):
        res = auth_client_a.patch(tx_url(tx_b.id), {"amount": "1.00"})
        assert res.status_code == status.HTTP_404_NOT_FOUND
        tx_b.refresh_from_db()
        assert float(tx_b.amount) == 99.00

    def test_cannot_assign_other_users_category(self, auth_client_a, tx_a, cat_b_expense):
        assert auth_client_a.patch(tx_url(tx_a.id), {"category": cat_b_expense.id}).status_code == status.HTTP_400_BAD_REQUEST


class TestTransactionDelete:
    def test_delete_own_transaction(self, auth_client_a, tx_a):
        res = auth_client_a.delete(tx_url(tx_a.id))
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not Transaction.objects.filter(id=tx_a.id).exists()

    def test_idor_cannot_delete_other_users_transaction(self, auth_client_a, tx_b):
        assert auth_client_a.delete(tx_url(tx_b.id)).status_code == status.HTTP_404_NOT_FOUND
        assert Transaction.objects.filter(id=tx_b.id).exists()


class TestCategoryOwnership:
    def test_cannot_create_transaction_with_other_users_category(self, auth_client_a, cat_b_expense):
        res = auth_client_a.post(TRANSACTIONS_URL, {
            "type": "expense", "amount": "10.00",
            "date": "2024-06-01", "category": cat_b_expense.id,
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST


# ─────────────────────────────────────────────────────────────────────────────────
# CSV export
# ─────────────────────────────────────────────────────────────────────────────────
class TestCSVExport:
    def test_returns_csv_content_type(self, auth_client_a, tx_a):
        res = auth_client_a.get(EXPORT_URL)
        assert res.status_code == status.HTTP_200_OK
        assert "text/csv" in res["Content-Type"]
        assert 'attachment' in res["Content-Disposition"]

    def test_csv_contains_header_row(self, auth_client_a, tx_a):
        res    = auth_client_a.get(EXPORT_URL)
        reader = csv.reader(io.StringIO(b"".join(res.streaming_content).decode()))
        header = next(reader)
        assert header == ["date", "type", "amount", "category", "note"]

    def test_csv_contains_transaction_data(self, auth_client_a, tx_a):
        res    = auth_client_a.get(EXPORT_URL)
        reader = csv.reader(io.StringIO(b"".join(res.streaming_content).decode()))
        next(reader)   # skip header
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0][1] == "expense"
        assert rows[0][2] == "50.00"

    def test_csv_excludes_other_users_transactions(self, auth_client_a, tx_a, tx_b):
        res    = auth_client_a.get(EXPORT_URL)
        reader = csv.reader(io.StringIO(b"".join(res.streaming_content).decode()))
        next(reader)
        rows = list(reader)
        assert len(rows) == 1   # only tx_a, not tx_b

    def test_csv_respects_type_filter(self, auth_client_a, user_a, cat_a_expense, cat_a_income):
        Transaction.objects.create(user=user_a, type="income",  amount="500.00",
                                   date=datetime.date.today(), category=cat_a_income)
        Transaction.objects.create(user=user_a, type="expense", amount="20.00",
                                   date=datetime.date.today(), category=cat_a_expense)
        res    = auth_client_a.get(EXPORT_URL + "?type=income")
        reader = csv.reader(io.StringIO(b"".join(res.streaming_content).decode()))
        next(reader)
        rows = list(reader)
        assert all(r[1] == "income" for r in rows)

    def test_unauthenticated_rejected(self, api_client, db):
        assert api_client.get(EXPORT_URL).status_code == status.HTTP_401_UNAUTHORIZED


# ─────────────────────────────────────────────────────────────────────────────────
# Budget limits
# ─────────────────────────────────────────────────────────────────────────────────
class TestBudgetCRUD:
    def test_create_budget(self, auth_client_a, user_a, cat_a_expense):
        res = auth_client_a.post(BUDGETS_URL, {"category": cat_a_expense.id, "monthly_limit": "500.00"})
        assert res.status_code == status.HTTP_201_CREATED
        assert Budget.objects.filter(user=user_a, category=cat_a_expense).exists()

    def test_list_own_budgets(self, auth_client_a, user_a, cat_a_expense):
        Budget.objects.create(user=user_a, category=cat_a_expense, monthly_limit="300.00")
        res = auth_client_a.get(BUDGETS_URL)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1

    def test_duplicate_category_rejected(self, auth_client_a, user_a, cat_a_expense):
        Budget.objects.create(user=user_a, category=cat_a_expense, monthly_limit="300.00")
        res = auth_client_a.post(BUDGETS_URL, {"category": cat_a_expense.id, "monthly_limit": "400.00"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_use_other_users_category(self, auth_client_a, cat_b_expense):
        res = auth_client_a.post(BUDGETS_URL, {"category": cat_b_expense.id, "monthly_limit": "100.00"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_monthly_limit(self, auth_client_a, user_a, cat_a_expense):
        budget = Budget.objects.create(user=user_a, category=cat_a_expense, monthly_limit="300.00")
        res = auth_client_a.patch(budget_url(budget.id), {"monthly_limit": "600.00"})
        assert res.status_code == status.HTTP_200_OK
        budget.refresh_from_db()
        assert float(budget.monthly_limit) == 600.00

    def test_idor_cannot_access_other_users_budget(self, auth_client_a, user_b, cat_b_expense):
        budget = Budget.objects.create(user=user_b, category=cat_b_expense, monthly_limit="200.00")
        assert auth_client_a.get(budget_url(budget.id)).status_code == status.HTTP_404_NOT_FOUND

    def test_delete_own_budget(self, auth_client_a, user_a, cat_a_expense):
        budget = Budget.objects.create(user=user_a, category=cat_a_expense, monthly_limit="300.00")
        res = auth_client_a.delete(budget_url(budget.id))
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_unauthenticated_rejected(self, api_client, db):
        assert api_client.get(BUDGETS_URL).status_code == status.HTTP_401_UNAUTHORIZED


class TestBudgetStatus:
    BUDGET_STATUS_URL = "/api/analytics/budget-status/"

    def test_returns_spent_and_remaining(self, auth_client_a, user_a, cat_a_expense):
        Budget.objects.create(user=user_a, category=cat_a_expense, monthly_limit="500.00")
        Transaction.objects.create(user=user_a, type="expense", amount="200.00",
                                   date=datetime.date.today(), category=cat_a_expense)
        res = auth_client_a.get(self.BUDGET_STATUS_URL)
        assert res.status_code == status.HTTP_200_OK
        row = res.data[0]
        assert float(row["monthly_limit"]) == 500.00
        assert float(row["spent"])         == 200.00
        assert float(row["remaining"])     == 300.00
        assert row["percent_used"]         == 40.0

    def test_no_budgets_returns_empty_list(self, auth_client_a, db):
        res = auth_client_a.get(self.BUDGET_STATUS_URL)
        assert res.status_code == status.HTTP_200_OK
        assert res.data == []

    def test_only_current_month_expenses_counted(self, auth_client_a, user_a, cat_a_expense):
        Budget.objects.create(user=user_a, category=cat_a_expense, monthly_limit="500.00")
        # Old expense — should NOT count toward this month's budget
        Transaction.objects.create(user=user_a, type="expense", amount="999.00",
                                   date=datetime.date(2020, 1, 1), category=cat_a_expense)
        res = auth_client_a.get(self.BUDGET_STATUS_URL)
        assert float(res.data[0]["spent"]) == 0

    def test_unauthenticated_rejected(self, api_client, db):
        assert api_client.get(self.BUDGET_STATUS_URL).status_code == status.HTTP_401_UNAUTHORIZED


# ─────────────────────────────────────────────────────────────────────────────────
# Recurring transactions
# ─────────────────────────────────────────────────────────────────────────────────
class TestRecurringCRUD:
    def _payload(self, cat_id, interval="monthly"):
        return {
            "type": "expense", "amount": "100.00", "note": "rent",
            "category": cat_id, "interval": interval,
            "next_occurrence": "2025-06-01",
        }

    def test_create_recurring(self, auth_client_a, user_a, cat_a_expense):
        res = auth_client_a.post(RECURRING_URL, self._payload(cat_a_expense.id))
        assert res.status_code == status.HTTP_201_CREATED
        assert RecurringTransaction.objects.filter(user=user_a).exists()

    def test_list_own_schedules(self, auth_client_a, user_a, cat_a_expense):
        RecurringTransaction.objects.create(
            user=user_a, category=cat_a_expense, type="expense",
            amount="100.00", interval="monthly", next_occurrence="2025-06-01",
        )
        res = auth_client_a.get(RECURRING_URL)
        assert res.status_code == status.HTTP_200_OK and len(res.data) == 1

    def test_idor_cannot_access_other_users_schedule(self, auth_client_a, user_b, cat_b_expense):
        rt = RecurringTransaction.objects.create(
            user=user_b, category=cat_b_expense, type="expense",
            amount="50.00", interval="weekly", next_occurrence="2025-06-01",
        )
        assert auth_client_a.get(recurring_url(rt.id)).status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_use_other_users_category(self, auth_client_a, cat_b_expense):
        res = auth_client_a.post(RECURRING_URL, self._payload(cat_b_expense.id))
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_is_active_to_pause(self, auth_client_a, user_a, cat_a_expense):
        rt = RecurringTransaction.objects.create(
            user=user_a, category=cat_a_expense, type="expense",
            amount="100.00", interval="monthly", next_occurrence="2025-06-01",
        )
        res = auth_client_a.patch(recurring_url(rt.id), {"is_active": False})
        assert res.status_code == status.HTTP_200_OK
        rt.refresh_from_db()
        assert rt.is_active is False

    def test_delete_schedule(self, auth_client_a, user_a, cat_a_expense):
        rt = RecurringTransaction.objects.create(
            user=user_a, category=cat_a_expense, type="expense",
            amount="100.00", interval="monthly", next_occurrence="2025-06-01",
        )
        assert auth_client_a.delete(recurring_url(rt.id)).status_code == status.HTTP_204_NO_CONTENT

    def test_unauthenticated_rejected(self, api_client, db):
        assert api_client.get(RECURRING_URL).status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLazyRecurringProcessing:
    """
    GET /api/transactions/ fires process_recurring_for_user before returning
    results — so no cron job is needed.
    """

    def _make_due(self, user, category, interval="monthly", days_overdue=1):
        due_date = datetime.date.today() - datetime.timedelta(days=days_overdue)
        return RecurringTransaction.objects.create(
            user=user, category=category, type="expense",
            amount="75.00", note="auto", interval=interval,
            next_occurrence=due_date, is_active=True,
        )

    def test_due_recurring_creates_transaction_on_list(self, auth_client_a, user_a, cat_a_expense):
        self._make_due(user_a, cat_a_expense)
        assert Transaction.objects.filter(user=user_a).count() == 0

        res = auth_client_a.get(TRANSACTIONS_URL)

        assert res.status_code == status.HTTP_200_OK
        assert Transaction.objects.filter(user=user_a).count() == 1

    def test_next_occurrence_advances_after_list(self, auth_client_a, user_a, cat_a_expense):
        rt = self._make_due(user_a, cat_a_expense, interval="weekly")
        original = rt.next_occurrence

        auth_client_a.get(TRANSACTIONS_URL)

        rt.refresh_from_db()
        assert rt.next_occurrence == original + datetime.timedelta(weeks=1)

    def test_paused_schedule_not_processed(self, auth_client_a, user_a, cat_a_expense):
        rt = self._make_due(user_a, cat_a_expense)
        rt.is_active = False
        rt.save()

        auth_client_a.get(TRANSACTIONS_URL)

        assert Transaction.objects.filter(user=user_a).count() == 0

    def test_future_schedule_not_processed(self, auth_client_a, user_a, cat_a_expense):
        future = datetime.date.today() + datetime.timedelta(days=7)
        RecurringTransaction.objects.create(
            user=user_a, category=cat_a_expense, type="expense",
            amount="50.00", interval="monthly", next_occurrence=future, is_active=True,
        )
        auth_client_a.get(TRANSACTIONS_URL)
        assert Transaction.objects.filter(user=user_a).count() == 0

    def test_only_own_schedules_processed(self, auth_client_a, user_b, cat_b_expense):
        self._make_due(user_b, cat_b_expense)
        auth_client_a.get(TRANSACTIONS_URL)
        assert Transaction.objects.filter(user=user_b).count() == 0
