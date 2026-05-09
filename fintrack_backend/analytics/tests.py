"""
Analytics endpoint tests
─────────────────────────
Covers:
  /api/analytics/summary/      — totals, empty state, date filter, data isolation
  /api/analytics/by-category/  — expense & income breakdown, uncategorised label,
                                  empty state, data isolation
  /api/analytics/over-time/    — monthly & daily aggregation, date filter,
                                  empty state, data isolation
"""

import datetime
import pytest
from rest_framework import status
from transactions.models import Transaction

SUMMARY_URL     = "/api/analytics/summary/"
BY_CATEGORY_URL = "/api/analytics/by-category/"
OVER_TIME_URL   = "/api/analytics/over-time/"


# ── Shared seed data ──────────────────────────────────────────────────────────────
@pytest.fixture
def seeded(user_a, cat_a_expense, cat_a_income):
    """Three transactions for alice across May 2024: one income, two expenses."""
    Transaction.objects.bulk_create([
        Transaction(user=user_a, type="income",  amount=3000,
                    date=datetime.date(2024, 5,  1), category=cat_a_income),
        Transaction(user=user_a, type="expense", amount=200,
                    date=datetime.date(2024, 5, 10), category=cat_a_expense),
        Transaction(user=user_a, type="expense", amount=50,
                    date=datetime.date(2024, 5, 20), category=cat_a_expense),
    ])


# ── Summary ───────────────────────────────────────────────────────────────────────
class TestSummary:
    def test_correct_totals(self, auth_client_a, seeded):
        res = auth_client_a.get(SUMMARY_URL)
        assert res.status_code == status.HTTP_200_OK
        assert float(res.data["total_income"])   == 3000
        assert float(res.data["total_expenses"]) == 250
        assert float(res.data["balance"])        == 2750

    def test_empty_returns_zeros(self, auth_client_a, db):
        res = auth_client_a.get(SUMMARY_URL)
        assert res.status_code == status.HTTP_200_OK
        assert float(res.data["total_income"])   == 0
        assert float(res.data["total_expenses"]) == 0
        assert float(res.data["balance"])        == 0

    def test_date_range_filter_excludes_out_of_range(self, auth_client_a, seeded):
        # Only May 10 and May 20 expenses are in range; income on May 1 is excluded
        res = auth_client_a.get(SUMMARY_URL + "?from=2024-05-05&to=2024-05-31")
        assert res.status_code == status.HTTP_200_OK
        assert float(res.data["total_income"])   == 0
        assert float(res.data["total_expenses"]) == 250

    def test_data_isolation_other_users_tx_excluded(self, auth_client_a, seeded, tx_b):
        """Bob's 99.00 expense must NOT inflate alice's total_expenses."""
        res = auth_client_a.get(SUMMARY_URL)
        assert float(res.data["total_expenses"]) == 250  # not 349

    def test_unauthenticated_rejected(self, api_client, db):
        res = api_client.get(SUMMARY_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ── By-category ───────────────────────────────────────────────────────────────────
class TestByCategory:
    def test_expense_breakdown_correct(self, auth_client_a, seeded):
        res = auth_client_a.get(BY_CATEGORY_URL + "?type=expense")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]["category"] == "Food"
        assert float(res.data[0]["total"]) == 250

    def test_income_breakdown_correct(self, auth_client_a, seeded):
        res = auth_client_a.get(BY_CATEGORY_URL + "?type=income")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]["category"] == "Salary"
        assert float(res.data[0]["total"]) == 3000

    def test_empty_returns_empty_list(self, auth_client_a, db):
        res = auth_client_a.get(BY_CATEGORY_URL)
        assert res.status_code == status.HTTP_200_OK
        assert res.data == []

    def test_uncategorised_label_used_for_null_category(self, auth_client_a, user_a, db):
        Transaction.objects.create(
            user=user_a, type="expense", amount="15.00",
            date=datetime.date.today(), category=None,
        )
        res = auth_client_a.get(BY_CATEGORY_URL + "?type=expense")
        categories = [row["category"] for row in res.data]
        assert "Uncategorised" in categories

    def test_data_isolation_other_users_categories_excluded(
        self, auth_client_a, seeded, cat_b_expense, tx_b
    ):
        """Bob's 'Travel' category must NOT appear in alice's breakdown."""
        res = auth_client_a.get(BY_CATEGORY_URL + "?type=expense")
        categories = [row["category"] for row in res.data]
        assert "Travel" not in categories

    def test_unauthenticated_rejected(self, api_client, db):
        res = api_client.get(BY_CATEGORY_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ── Over-time ─────────────────────────────────────────────────────────────────────
class TestOverTime:
    def test_monthly_aggregation(self, auth_client_a, seeded):
        res = auth_client_a.get(OVER_TIME_URL + "?period=month")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1        # all in May 2024
        row = res.data[0]
        assert float(row["income"])   == 3000
        assert float(row["expenses"]) == 250
        assert float(row["balance"])  == 2750

    def test_daily_aggregation_three_distinct_days(self, auth_client_a, seeded):
        res = auth_client_a.get(OVER_TIME_URL + "?period=day")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 3        # May 1, May 10, May 20

    def test_date_filter_narrows_to_single_day(self, auth_client_a, seeded):
        res = auth_client_a.get(
            OVER_TIME_URL + "?period=day&from=2024-05-01&to=2024-05-01"
        )
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert float(res.data[0]["income"])   == 3000
        assert float(res.data[0]["expenses"]) == 0

    def test_empty_returns_empty_list(self, auth_client_a, db):
        res = auth_client_a.get(OVER_TIME_URL)
        assert res.status_code == status.HTTP_200_OK
        assert res.data == []

    def test_data_isolation_other_users_excluded(self, auth_client_a, seeded, tx_b):
        """Bob's 99.00 expense must NOT appear in alice's monthly totals."""
        res = auth_client_a.get(OVER_TIME_URL + "?period=month")
        for row in res.data:
            assert float(row["expenses"]) == 250  # not 349

    def test_unauthenticated_rejected(self, api_client, db):
        res = api_client.get(OVER_TIME_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
