"""
Auth endpoint tests
───────────────────
Covers: register, login, /me, logout + token blacklist, token refresh.
All fixtures live in the root conftest.py.
"""

import pytest
from rest_framework import status

REGISTER_URL = "/api/auth/register/"
LOGIN_URL    = "/api/auth/login/"
LOGOUT_URL   = "/api/auth/logout/"
REFRESH_URL  = "/api/auth/refresh/"
ME_URL       = "/api/auth/me/"

VALID_REG = {
    "username":  "alice",
    "email":     "alice@example.com",
    "password":  "StrongPass123!",
    "password2": "StrongPass123!",
}


# ── Registration ──────────────────────────────────────────────────────────────────
class TestRegister:
    def test_success_creates_user(self, api_client, db):
        res = api_client.post(REGISTER_URL, VALID_REG)
        assert res.status_code == status.HTTP_201_CREATED
        # password must never be returned
        assert "password" not in res.data

    def test_password_mismatch_rejected(self, api_client, db):
        data = {**VALID_REG, "password2": "Mismatch999!"}
        res = api_client.post(REGISTER_URL, data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_username_rejected(self, api_client, user_a):
        # user_a is already "alice"
        data = {**VALID_REG, "email": "other@example.com"}
        res = api_client.post(REGISTER_URL, data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_email_rejected(self, api_client, user_a):
        data = {**VALID_REG, "username": "different"}
        res = api_client.post(REGISTER_URL, data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_weak_password_rejected(self, api_client, db):
        data = {
            "username": "newuser", "email": "new@example.com",
            "password": "123", "password2": "123",
        }
        res = api_client.post(REGISTER_URL, data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_required_fields_rejected(self, api_client, db):
        res = api_client.post(REGISTER_URL, {"username": "x"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST


# ── Login ─────────────────────────────────────────────────────────────────────────
class TestLogin:
    def test_success_returns_access_and_refresh(self, api_client, user_a):
        res = api_client.post(LOGIN_URL, {"username": "alice", "password": "StrongPass123!"})
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.data
        assert "refresh" in res.data

    def test_wrong_password_rejected(self, api_client, user_a):
        res = api_client.post(LOGIN_URL, {"username": "alice", "password": "wrong"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_user_rejected(self, api_client, db):
        res = api_client.post(LOGIN_URL, {"username": "nobody", "password": "anything"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_password_rejected(self, api_client, user_a):
        res = api_client.post(LOGIN_URL, {"username": "alice"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST


# ── /me endpoint ──────────────────────────────────────────────────────────────────
class TestMe:
    def test_authenticated_returns_profile(self, auth_client_a, user_a):
        res = auth_client_a.get(ME_URL)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["username"] == "alice"
        assert res.data["email"] == "alice@example.com"
        assert "password" not in res.data

    def test_unauthenticated_rejected(self, api_client):
        res = api_client.get(ME_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_own_data_not_other_users(self, auth_client_a, auth_client_b):
        res = auth_client_a.get(ME_URL)
        assert res.data["username"] == "alice"
        res2 = auth_client_b.get(ME_URL)
        assert res2.data["username"] == "bob"


# ── Logout & token blacklist ───────────────────────────────────────────────────────
class TestLogout:
    def test_logout_succeeds(self, auth_client_a):
        res = auth_client_a.post(LOGOUT_URL, {"refresh": auth_client_a._refresh_token})
        assert res.status_code == status.HTTP_205_RESET_CONTENT

    def test_blacklisted_refresh_token_cannot_be_used(self, auth_client_a, api_client):
        refresh = auth_client_a._refresh_token
        auth_client_a.post(LOGOUT_URL, {"refresh": refresh})
        # The old refresh token must now be dead
        res = api_client.post(REFRESH_URL, {"refresh": refresh})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_without_refresh_token_rejected(self, auth_client_a):
        res = auth_client_a.post(LOGOUT_URL, {})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_already_blacklisted_token_is_idempotent(self, auth_client_a):
        """Logging out twice with the same token returns 205, not 500."""
        refresh = auth_client_a._refresh_token
        auth_client_a.post(LOGOUT_URL, {"refresh": refresh})
        res = auth_client_a.post(LOGOUT_URL, {"refresh": refresh})
        assert res.status_code == status.HTTP_205_RESET_CONTENT

    def test_unauthenticated_cannot_logout(self, api_client, db):
        res = api_client.post(LOGOUT_URL, {"refresh": "sometoken"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ── Token refresh ─────────────────────────────────────────────────────────────────
class TestTokenRefresh:
    def test_valid_refresh_returns_new_access_token(self, auth_client_a):
        res = auth_client_a.post(REFRESH_URL, {"refresh": auth_client_a._refresh_token})
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.data

    def test_invalid_refresh_token_rejected(self, api_client, db):
        res = api_client.post(REFRESH_URL, {"refresh": "not.a.valid.token"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
