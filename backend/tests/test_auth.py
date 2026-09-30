"""
Auth tests.

Shared DB, dependency override, and per-test seeding live in
tests/conftest.py. Do not add module-level env vars or engine setup here.

Run with: pytest tests/test_auth.py -v
"""
import datetime
import os

import jwt
from fastapi.testclient import TestClient

from main import app

# These env vars are set by tests/conftest.py, which pytest imports first.
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_HANDLE = os.environ["ADMIN_HANDLE"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]

# The DB dependency override is already installed by conftest, so this client
# talks to the shared in-memory DB.
client = TestClient(app, raise_server_exceptions=False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def register(email="user@test.com", handle="TestUser", password="password123"):
    return client.post("/api/register", json={
        "email": email, "handle": handle, "password": password,
    })


def login(email="user@test.com", password="password123"):
    return client.post("/api/login", json={"email": email, "password": password})


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def login_as_admin():
    return client.post("/api/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
    })


# ── Registration ──────────────────────────────────────────────────────────────

def test_register_success():
    r = register()
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "user@test.com"
    assert data["handle"] == "TestUser"
    assert data["role"] == "USER"
    assert "password_hash" not in data


def test_register_duplicate_email():
    register()
    r = register(handle="OtherHandle")
    assert r.status_code == 409
    assert "email" in r.json()["detail"].lower()


def test_register_duplicate_handle_case_insensitive():
    register(handle="TestUser")
    r = register(email="other@test.com", handle="testuser")
    assert r.status_code == 409
    assert "handle" in r.json()["detail"].lower()


def test_register_invalid_handle_too_short():
    r = register(handle="ab")
    assert r.status_code == 422


def test_register_invalid_handle_bad_chars():
    r = register(handle="bad handle")
    assert r.status_code == 422


def test_register_handle_boundary_ok():
    assert register(email="a@test.com", handle="abc").status_code == 201
    assert register(email="b@test.com", handle="a" * 20).status_code == 201


def test_register_short_password():
    r = register(password="short")
    assert r.status_code == 422


def test_register_password_boundary_ok():
    r = register(password="12345678")
    assert r.status_code == 201


def test_register_invalid_email():
    r = register(email="not-an-email")
    assert r.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_success():
    register()
    r = login()
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password():
    register()
    r = login(password="wrongpassword")
    assert r.status_code == 401


def test_login_unknown_email():
    r = login(email="nobody@test.com")
    assert r.status_code == 401


def test_login_same_message_for_wrong_password_and_unknown_email():
    register()
    r1 = login(password="wrongpassword")
    r2 = login(email="nobody@test.com")
    assert r1.json()["detail"] == r2.json()["detail"]


def test_login_token_role_is_uppercase():
    """Regression test: role claim must be uppercase, matching UserRole.name
    and _VALID_ROLES in security.py."""
    register()
    token = login().json()["access_token"]
    payload = jwt.decode(token, os.environ["SECRET_KEY"], algorithms=["HS256"])
    assert payload["role"] == "USER"
    assert payload["sub"].isdigit()


# ── /api/me ───────────────────────────────────────────────────────────────────

def test_me_no_token():
    r = client.get("/api/me")
    assert r.status_code == 401


def test_me_garbage_token():
    r = client.get("/api/me", headers={"Authorization": "Bearer notavalidtoken"})
    assert r.status_code == 401


def test_me_malformed_header():
    r = client.get("/api/me", headers={"Authorization": "Token abc"})
    assert r.status_code == 401


def test_me_expired_token():
    expired = jwt.encode(
        {
            "sub": "999",
            "role": "USER",
            "exp": datetime.datetime.now(datetime.timezone.utc)
                   - datetime.timedelta(hours=1),
        },
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )
    r = client.get("/api/me", headers=auth_header(expired))
    assert r.status_code == 401


def test_me_token_for_deleted_user():
    """A valid, unexpired token whose user no longer exists must 401."""
    token = jwt.encode(
        {
            "sub": "999999",
            "role": "USER",
            "exp": datetime.datetime.now(datetime.timezone.utc)
                   + datetime.timedelta(hours=1),
        },
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )
    r = client.get("/api/me", headers=auth_header(token))
    assert r.status_code == 401


def test_me_success():
    register()
    token = login().json()["access_token"]
    r = client.get("/api/me", headers=auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["handle"] == "TestUser"
    assert body["role"] == "USER"
    assert "password_hash" not in body


# ── Handle change ─────────────────────────────────────────────────────────────

def test_change_handle_to_new():
    register(handle="oldhandle")
    token = login().json()["access_token"]
    r = client.patch("/api/me/handle",
                     json={"handle": "newhandle"},
                     headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["handle"] == "newhandle"


def test_change_handle_to_taken():
    register(handle="alice")
    register(email="bob@test.com", handle="bob")
    token = login().json()["access_token"]   # logs in as alice
    r = client.patch("/api/me/handle",
                     json={"handle": "bob"},
                     headers=auth_header(token))
    assert r.status_code == 409


def test_change_handle_own_capitalization():
    register(handle="myhandle")
    token = login().json()["access_token"]
    r = client.patch("/api/me/handle",
                     json={"handle": "MyHandle"},
                     headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["handle"] == "MyHandle"


def test_change_handle_requires_auth():
    r = client.patch("/api/me/handle", json={"handle": "newhandle"})
    assert r.status_code == 401


def test_admin_cannot_change_handle():
    token = login_as_admin().json()["access_token"]
    r = client.patch("/api/me/handle",
                     json={"handle": "newhandle"},
                     headers=auth_header(token))
    assert r.status_code == 403


# ── Password change ───────────────────────────────────────────────────────────

def test_change_password_wrong_current():
    register()
    token = login().json()["access_token"]
    r = client.patch("/api/me/password", json={
        "current_password": "wrongpassword",
        "new_password": "newpassword123",
    }, headers=auth_header(token))
    assert r.status_code == 401


def test_change_password_too_short_new():
    register()
    token = login().json()["access_token"]
    r = client.patch("/api/me/password", json={
        "current_password": "password123",
        "new_password": "short",
    }, headers=auth_header(token))
    assert r.status_code == 422


def test_change_password_roundtrip():
    register()
    token = login().json()["access_token"]

    r = client.patch("/api/me/password", json={
        "current_password": "password123",
        "new_password": "brandnewpass456",
    }, headers=auth_header(token))
    assert r.status_code == 200

    assert login(password="password123").status_code == 401
    assert login(password="brandnewpass456").status_code == 200


def test_admin_cannot_change_password():
    token = login_as_admin().json()["access_token"]
    r = client.patch("/api/me/password", json={
        "current_password": ADMIN_PASSWORD,
        "new_password": "newpassword123",
    }, headers=auth_header(token))
    assert r.status_code == 403