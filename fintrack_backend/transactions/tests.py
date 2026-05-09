"""
Transaction & category endpoint tests
──────────────────────────────────────
Covers:
  Category  — create, list (user-scoped), delete own vs. IDOR
  Transaction — create, list (user-scoped), retrieve (IDOR), update own vs. IDOR,
                delete own vs. IDOR, date/type/category filters, malformed input
  Category ownership — cannot assign another user's category to a transaction
"""

import datetime
import pytest
from rest_framework import status
from transactions.models import Category, Transaction

CATEGORIES_URL   = "/api/categories/"
TRANSACTIONS_URL = "/api/transactions/"


def cat_url(pk):
    return f"/api/categories/{pk}/"


def tx_url(pk):
    return f"/api/transactions/{pk}/"


# ── Category: create ──────────────────────────────────────────────────────────────
class TestCategoryCreate:
    def test_create_expense_category(self, auth_client_a, user_a):
        res = auth_client_a.post(CATEGORIES_URL, {"name": "Rent", "type": "expense"})
        assert res.status_code == status.HTTP_201_CREATED
        assert Category.objects.filter(name="Rent", user=user_a).exists()

    def test_create_income_category(self, auth_client_a, user_a):
        res = auth_client_a.post(CATEGORIES_URL, {"name": "Freelance", "type": "income"})
        assert res.status_code == status.HTTP_201_CREATED

    def test_missing_type_rejected(self, auth_client_a):
        res = auth_client_a.post(CATEGORIES_URL, {"name": "Oops"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_type_rejected(self, auth_client_a):
        res = auth_client_a.post(CATEGORIES_URL, {"name": "Misc", "type": "neither"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_rejected(self, api_client, db):
        res = api_client.post(CATEGORIES_URL, {"name": "Rent", "type": "expense"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ── Category: list ────────────────────────────────────────────────────────────────
class TestCategoryList:
    def test_lists_only_own_categories(
        self, auth_client_a, cat_a_expense, cat_b_expense
    ):
        res = auth_client_a.get(CATEGORIES_URL)
        assert res.status_code == status.HTTP_200_OK
        names = [c["name"] for c in res.data]
        assert "Food"   in names       # alice's category
        assert "Travel" not in names   # bob's category — must be hidden

    def test_empty_list_when_no_categories(self, auth_client_a, db):
        res = auth_client_a.get(CATEGORIES_URL)
        assert res.status_code == status.HTTP_200_OK
        assert res.data == []


# ── Category: delete ──────────────────────────────────────────────────────────────
class TestCategoryDelete:
    def test_delete_own_category(self, auth_client_a, cat_a_expense):
        res = auth_client_a.delete(cat_url(cat_a_expense.id))
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not Category.objects.filter(id=cat_a_expense.id).exists()

    def test_idor_cannot_delete_other_users_category(self, auth_client_a, cat_b_expense):
        """Alice must get 404 — not 403 — to avoid confirming the resource exists."""
        res = auth_client_a.delete(cat_url(cat_b_expense.id))
        assert res.status_code == status.HTTP_404_NOT_FOUND
        assert Category.objects.filter(id=cat_b_expense.id).exists()  # still there

    def test_delete_nonexistent_category_returns_404(self, auth_client_a, db):
        res = auth_client_a.delete(cat_url(99999))
        assert res.status_code == status.HTTP_404_NOT_FOUND


# ── Transaction: create ───────────────────────────────────────────────────────────
class TestTransactionCreate:
    def test_create_expense(self, auth_client_a, user_a, cat_a_expense):
        data = {
            "type": "expense", "amount": "25.00",
            "date": "2024-06-01", "category": cat_a_expense.id, "note": "coffee",
        }
        res = auth_client_a.post(TRANSACTIONS_URL, data)
        assert res.status_code == status.HTTP_201_CREATED
        assert Transaction.objects.filter(user=user_a, note="coffee").exists()

    def test_create_income(self, auth_client_a, cat_a_income):
        data = {
            "type": "income", "amount": "3000.00",
            "date": "2024-06-01", "category": cat_a_income.id,
        }
        res = auth_client_a.post(TRANSACTIONS_URL, data)
        assert res.status_code == status.HTTP_201_CREATED

    def test_create_without_category_allowed(self, auth_client_a):
        data = {"type": "expense", "amount": "10.00", "date": "2024-06-01"}
        res = auth_client_a.post(TRANSACTIONS_URL, data)
        assert res.status_code == status.HTTP_201_CREATED

    def test_unauthenticated_rejected(self, api_client, db):
        data = {"type": "expense", "amount": "10.00", "date": "2024-06-01"}
        res = api_client.post(TRANSACTIONS_URL, data)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_amount_rejected(self, auth_client_a):
        data = {"type": "expense", "date": "2024-06-01"}
        res = auth_client_a.post(TRANSACTIONS_URL, data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_date_rejected(self, auth_client_a):
        data = {"type": "expense", "amount": "10.00"}
        res = auth_client_a.post(TRANSACTIONS_URL, data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST


# ── Transaction: list & filters ───────────────────────────────────────────────────
class TestTransactionList:
    def test_lists_only_own_transactions(self, auth_client_a, tx_a, tx_b):
        res = auth_client_a.get(TRANSACTIONS_URL)
        assert res.status_code == status.HTTP_200_OK
        ids = [t["id"] for t in res.data]
        assert tx_a.id in ids
        assert tx_b.id not in ids  # IDOR: bob's tx must never appear

    def test_filter_by_type_expense(self, auth_client_a, user_a, cat_a_expense, cat_a_income):
        Transaction.objects.create(user=user_a, type="expense", amount="20.00",
                                   date=datetime.date.today(), category=cat_a_expense)
        Transaction.objects.create(user=user_a, type="income", amount="500.00",
                                   date=datetime.date.today(), category=cat_a_income)
        res = auth_client_a.get(TRANSACTIONS_URL + "?type=expense")
        assert res.status_code == status.HTTP_200_OK
        assert all(t["type"] == "expense" for t in res.data)

    def test_filter_by_type_income(self, auth_client_a, user_a, cat_a_income, cat_a_expense):
        Transaction.objects.create(user=user_a, type="income", amount="500.00",
                                   date=datetime.date.today(), category=cat_a_income)
        Transaction.objects.create(user=user_a, type="expense", amount="20.00",
                                   date=datetime.date.today(), category=cat_a_expense)
        res = auth_client_a.get(TRANSACTIONS_URL + "?type=income")
        assert res.status_code == status.HTTP_200_OK
        assert all(t["type"] == "income" for t in res.data)

    def test_filter_by_date_range(self, auth_client_a, user_a):
        Transaction.objects.create(user=user_a, type="expense", amount="10.00",
                                   date=datetime.date(2024, 3, 1))
        Transaction.objects.create(user=user_a, type="expense", amount="20.00",
                                   date=datetime.date(2024, 5, 15))
        Transaction.objects.create(user=user_a, type="expense", amount="30.00",
                                   date=datetime.date(2024, 7, 1))
        res = auth_client_a.get(TRANSACTIONS_URL + "?from=2024-04-01&to=2024-06-30")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert float(res.data[0]["amount"]) == 20.00

    def test_filter_by_category(self, auth_client_a, user_a, cat_a_expense, cat_a_income):
        Transaction.objects.create(user=user_a, type="expense", amount="10.00",
                                   date=datetime.date.today(), category=cat_a_expense)
        Transaction.objects.create(user=user_a, type="income", amount="500.00",
                                   date=datetime.date.today(), category=cat_a_income)
        res = auth_client_a.get(TRANSACTIONS_URL + f"?category={cat_a_expense.id}")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]["category"] == cat_a_expense.id

    def test_malformed_date_does_not_500(self, auth_client_a, db):
        """Bad date params must be silently ignored, never cause a 500."""
        res = auth_client_a.get(TRANSACTIONS_URL + "?from=not-a-date&to=also-bad")
        assert res.status_code == status.HTTP_200_OK

    def test_unauthenticated_rejected(self, api_client, db):
        res = api_client.get(TRANSACTIONS_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ── Transaction: retrieve ─────────────────────────────────────────────────────────
class TestTransactionRetrieve:
    def test_retrieve_own_transaction(self, auth_client_a, tx_a):
        res = auth_client_a.get(tx_url(tx_a.id))
        assert res.status_code == status.HTTP_200_OK
        assert res.data["id"] == tx_a.id

    def test_idor_cannot_retrieve_other_users_transaction(self, auth_client_a, tx_b):
        """Alice must get 404 when requesting bob's transaction by ID."""
        res = auth_client_a.get(tx_url(tx_b.id))
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_nonexistent_transaction_returns_404(self, auth_client_a, db):
        res = auth_client_a.get(tx_url(99999))
        assert res.status_code == status.HTTP_404_NOT_FOUND


# ── Transaction: update ───────────────────────────────────────────────────────────
class TestTransactionUpdate:
    def test_patch_own_transaction_amount(self, auth_client_a, tx_a):
        res = auth_client_a.patch(tx_url(tx_a.id), {"amount": "75.00"})
        assert res.status_code == status.HTTP_200_OK
        tx_a.refresh_from_db()
        assert float(tx_a.amount) == 75.00

    def test_patch_own_transaction_note(self, auth_client_a, tx_a):
        res = auth_client_a.patch(tx_url(tx_a.id), {"note": "dinner"})
        assert res.status_code == status.HTTP_200_OK
        tx_a.refresh_from_db()
        assert tx_a.note == "dinner"

    def test_idor_cannot_patch_other_users_transaction(self, auth_client_a, tx_b):
        """Alice must get 404 — bob's transaction must remain unchanged."""
        res = auth_client_a.patch(tx_url(tx_b.id), {"amount": "1.00"})
        assert res.status_code == status.HTTP_404_NOT_FOUND
        tx_b.refresh_from_db()
        assert float(tx_b.amount) == 99.00  # unchanged

    def test_cannot_assign_other_users_category(self, auth_client_a, tx_a, cat_b_expense):
        """Category ownership: alice cannot reassign bob's category onto her transaction."""
        res = auth_client_a.patch(tx_url(tx_a.id), {"category": cat_b_expense.id})
        assert res.status_code == status.HTTP_400_BAD_REQUEST


# ── Transaction: delete ───────────────────────────────────────────────────────────
class TestTransactionDelete:
    def test_delete_own_transaction(self, auth_client_a, tx_a):
        res = auth_client_a.delete(tx_url(tx_a.id))
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not Transaction.objects.filter(id=tx_a.id).exists()

    def test_idor_cannot_delete_other_users_transaction(self, auth_client_a, tx_b):
        """Alice must get 404 — bob's transaction must not be deleted."""
        res = auth_client_a.delete(tx_url(tx_b.id))
        assert res.status_code == status.HTTP_404_NOT_FOUND
        assert Transaction.objects.filter(id=tx_b.id).exists()  # still there


# ── Category ownership on create ──────────────────────────────────────────────────
class TestCategoryOwnership:
    def test_cannot_create_transaction_with_other_users_category(
        self, auth_client_a, cat_b_expense
    ):
        """Alice must not be able to use bob's category when creating a transaction."""
        data = {
            "type": "expense", "amount": "10.00",
            "date": "2024-06-01", "category": cat_b_expense.id,
        }
        res = auth_client_a.post(TRANSACTIONS_URL, data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST
