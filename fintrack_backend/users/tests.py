"""
Auth + account-settings tests
──────────────────────────────
Covers: register, login, /me (GET + PATCH), logout + token blacklist, token refresh.
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
        assert "password" not in res.data

    def test_password_mismatch_rejected(self, api_client, db):
        res = api_client.post(REGISTER_URL, {**VALID_REG, "password2": "Mismatch999!"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_username_rejected(self, api_client, user_a):
        res = api_client.post(REGISTER_URL, {**VALID_REG, "email": "other@example.com"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_email_rejected(self, api_client, user_a):
        res = api_client.post(REGISTER_URL, {**VALID_REG, "username": "different"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_weak_password_rejected(self, api_client, db):
        data = {**VALID_REG, "username": "newuser", "email": "new@example.com",
                "password": "123", "password2": "123"}
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
        assert "access" in res.data and "refresh" in res.data

    def test_wrong_password_rejected(self, api_client, user_a):
        res = api_client.post(LOGIN_URL, {"username": "alice", "password": "wrong"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_user_rejected(self, api_client, db):
        res = api_client.post(LOGIN_URL, {"username": "nobody", "password": "anything"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_password_rejected(self, api_client, user_a):
        res = api_client.post(LOGIN_URL, {"username": "alice"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST


# ── GET /me ───────────────────────────────────────────────────────────────────────
class TestMe:
    def test_authenticated_returns_profile(self, auth_client_a):
        res = auth_client_a.get(ME_URL)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["username"] == "alice"
        assert res.data["email"]    == "alice@example.com"
        assert "password" not in res.data

    def test_unauthenticated_rejected(self, api_client):
        assert api_client.get(ME_URL).status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_own_data_not_other_users(self, auth_client_a, auth_client_b):
        assert auth_client_a.get(ME_URL).data["username"] == "alice"
        assert auth_client_b.get(ME_URL).data["username"] == "bob"


# ── PATCH /me — account settings ─────────────────────────────────────────────────
class TestUpdateMe:
    def test_change_email_succeeds(self, auth_client_a, user_a):
        res = auth_client_a.patch(ME_URL, {"email": "newalice@example.com"})
        assert res.status_code == status.HTTP_200_OK
        user_a.refresh_from_db()
        assert user_a.email == "newalice@example.com"

    def test_duplicate_email_rejected(self, auth_client_a, user_b):
        res = auth_client_a.patch(ME_URL, {"email": "bob@example.com"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_succeeds(self, auth_client_a, user_a, api_client):
        res = auth_client_a.patch(ME_URL, {
            "current_password": "StrongPass123!",
            "new_password":     "NewSecure456!",
        })
        assert res.status_code == status.HTTP_200_OK
        # Old password must no longer work
        bad = api_client.post(LOGIN_URL, {"username": "alice", "password": "StrongPass123!"})
        assert bad.status_code == status.HTTP_401_UNAUTHORIZED
        # New password must work
        ok = api_client.post(LOGIN_URL, {"username": "alice", "password": "NewSecure456!"})
        assert ok.status_code == status.HTTP_200_OK

    def test_change_password_requires_current_password(self, auth_client_a):
        res = auth_client_a.patch(ME_URL, {"new_password": "NewSecure456!"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_wrong_current_password_rejected(self, auth_client_a):
        res = auth_client_a.patch(ME_URL, {
            "current_password": "WrongPass!",
            "new_password":     "NewSecure456!",
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_weak_new_password_rejected(self, auth_client_a):
        res = auth_client_a.patch(ME_URL, {
            "current_password": "StrongPass123!",
            "new_password":     "123",
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_rejected(self, api_client, db):
        assert api_client.patch(ME_URL, {"email": "x@x.com"}).status_code == status.HTTP_401_UNAUTHORIZED


# ── Logout & token blacklist ───────────────────────────────────────────────────────
class TestLogout:
    def test_logout_succeeds(self, auth_client_a):
        res = auth_client_a.post(LOGOUT_URL, {"refresh": auth_client_a._refresh_token})
        assert res.status_code == status.HTTP_205_RESET_CONTENT

    def test_blacklisted_refresh_token_cannot_be_used(self, auth_client_a, api_client):
        refresh = auth_client_a._refresh_token
        auth_client_a.post(LOGOUT_URL, {"refresh": refresh})
        assert api_client.post(REFRESH_URL, {"refresh": refresh}).status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_without_refresh_token_rejected(self, auth_client_a):
        assert auth_client_a.post(LOGOUT_URL, {}).status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_already_blacklisted_token_is_idempotent(self, auth_client_a):
        refresh = auth_client_a._refresh_token
        auth_client_a.post(LOGOUT_URL, {"refresh": refresh})
        assert auth_client_a.post(LOGOUT_URL, {"refresh": refresh}).status_code == status.HTTP_205_RESET_CONTENT

    def test_unauthenticated_cannot_logout(self, api_client, db):
        assert api_client.post(LOGOUT_URL, {"refresh": "tok"}).status_code == status.HTTP_401_UNAUTHORIZED


# ── Token refresh ─────────────────────────────────────────────────────────────────
class TestTokenRefresh:
    def test_valid_refresh_returns_new_access_token(self, auth_client_a):
        res = auth_client_a.post(REFRESH_URL, {"refresh": auth_client_a._refresh_token})
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.data

    def test_invalid_refresh_token_rejected(self, api_client, db):
        assert api_client.post(REFRESH_URL, {"refresh": "bad.token"}).status_code == status.HTTP_401_UNAUTHORIZED
