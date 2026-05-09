"""
Root conftest.py — shared fixtures available to all test modules.

Fixtures provided
─────────────────
api_client          Raw, unauthenticated APIClient
user_a              User "alice" (DB-backed)
user_b              User "bob"   (DB-backed)
auth_client_a       APIClient authenticated as alice; .refresh_token stored for logout tests
auth_client_b       APIClient authenticated as bob
cat_a_expense       Category owned by alice (Food / expense)
cat_a_income        Category owned by alice (Salary / income)
cat_b_expense       Category owned by bob   (Travel / expense)
tx_a                Single transaction owned by alice (expense, Food, 50.00, 2024-05-01)
tx_b                Single transaction owned by bob   (expense, Travel, 99.00, 2024-05-01)
"""

import datetime
import pytest
from rest_framework.test import APIClient
from users.models import User
from transactions.models import Category, Transaction


# ── Disable throttling globally so rate-limit state never bleeds between tests ──
#
# Two-part approach:
#   1. Clear the in-memory throttle cache before (and after) every test so that
#      per-IP history accumulated in earlier tests can't trigger a 429.
#   2. Set every rate to a huge number so even if cache clearing were incomplete
#      the views would still accept requests.
#
# This is necessary because ThrottledTokenObtainPairView and RegisterView set
# throttle_classes *on the view class*, not in DEFAULT_THROTTLE_CLASSES, so
# overriding settings alone isn't enough — the cache must also be clean.
@pytest.fixture(autouse=True)
def disable_throttling(settings):
    from django.core.cache import cache
    cache.clear()
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {
            "auth_login":    "99999/minute",
            "auth_register": "99999/hour",
            "anon":          "99999/day",
            "user":          "99999/day",
        },
    }
    yield
    cache.clear()


# ── Clients ─────────────────────────────────────────────────────────────────────
@pytest.fixture
def api_client():
    """Unauthenticated REST API client."""
    return APIClient()


# ── Users ────────────────────────────────────────────────────────────────────────
@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        username="alice", password="StrongPass123!", email="alice@example.com"
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        username="bob", password="StrongPass123!", email="bob@example.com"
    )


# ── Auth helpers ─────────────────────────────────────────────────────────────────
def _login(client, username, password):
    res = client.post("/api/auth/login/", {"username": username, "password": password})
    return res.data["access"], res.data["refresh"]


@pytest.fixture
def auth_client_a(api_client, user_a):
    """APIClient authenticated as alice. Stores refresh token at ._refresh_token."""
    access, refresh = _login(api_client, "alice", "StrongPass123!")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    api_client._refresh_token = refresh
    return api_client


@pytest.fixture
def auth_client_b(user_b):
    """APIClient authenticated as bob. Stores refresh token at ._refresh_token."""
    client = APIClient()
    access, refresh = _login(client, "bob", "StrongPass123!")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    client._refresh_token = refresh
    return client


# ── Categories ───────────────────────────────────────────────────────────────────
@pytest.fixture
def cat_a_expense(user_a):
    return Category.objects.create(name="Food", type="expense", user=user_a)


@pytest.fixture
def cat_a_income(user_a):
    return Category.objects.create(name="Salary", type="income", user=user_a)


@pytest.fixture
def cat_b_expense(user_b):
    return Category.objects.create(name="Travel", type="expense", user=user_b)


# ── Transactions ─────────────────────────────────────────────────────────────────
@pytest.fixture
def tx_a(user_a, cat_a_expense):
    return Transaction.objects.create(
        user=user_a,
        type="expense",
        amount="50.00",
        date=datetime.date(2024, 5, 1),
        category=cat_a_expense,
        note="lunch",
    )


@pytest.fixture
def tx_b(user_b, cat_b_expense):
    return Transaction.objects.create(
        user=user_b,
        type="expense",
        amount="99.00",
        date=datetime.date(2024, 5, 1),
        category=cat_b_expense,
    )
