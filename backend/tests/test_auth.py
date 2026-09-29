"""
Auth tests using FastAPI's TestClient against an in-memory SQLite database.

Run with: pytest tests/test_auth.py -v

Notes:
- Env vars are set before importing any app module, because security.py
  reads SECRET_KEY at import time and refuses to start without it.
- TestClient is instantiated at module level (not as a context manager),
  so main.py's lifespan — and therefore seed_admin() — does NOT run here.
  The fixture seeds the admin by hand instead. If you ever wrap the client
  in a `with` block, seed_admin() will run and try to connect to the real
  Postgres via SessionLocal, bypassing the get_db override.
"""
import os

os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ADMIN_EMAIL"] = "admin@test.com"
os.environ["ADMIN_HANDLE"] = "testadmin"
os.environ["ADMIN_PASSWORD"] = "adminpassword123"

import datetime
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, User, UserRole, get_db
from main import app
from security import hash_password

# ── Test database ─────────────────────────────────────────────────────────────

# In-memory SQLite. StaticPool makes all connections share one in-memory DB
# (otherwise each new connection would get its own empty database).
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Admin credentials come from the env vars set above — single source of truth.
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_HANDLE = os.environ["ADMIN_HANDLE"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]


@pytest.fixture(autouse=True)
def setup_db():
    """Fresh schema + admin user before each test; tear down after."""
    Base.metadata.create_all(bind=engine)

    db = TestSessionLocal()
    try:
        db.add(User(
            email=ADMIN_EMAIL,
            handle=ADMIN_HANDLE,
            handle_lower=ADMIN_HANDLE.lower(),
            password_hash=hash_password(ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        ))
        db.commit()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=engine)


# Replace the real DB dependency with our test DB.
app.dependency_overrides[get_db] = override_get_db

# raise_server_exceptions=False -> unhandled exceptions become 500 responses
# instead of being re-raised in the test. Set to True during active debugging
# to see full tracebacks instead of a mysterious 500 assertion.
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
    assert data["role"] == "USER"                 # uppercase on the wire
    assert "password_hash" not in data            # never leak the hash


def test_register_duplicate_email():
    register()
    r = register(handle="OtherHandle")
    assert r.status_code == 409
    assert "email" in r.json()["detail"].lower()


def test_register_duplicate_handle_case_insensitive():
    register(handle="TestUser")
    r = register(email="other@test.com", handle="testuser")   # different case
    assert r.status_code == 409
    assert "handle" in r.json()["detail"].lower()


def test_register_invalid_handle_too_short():
    r = register(handle="ab")
    assert r.status_code == 422


def test_register_invalid_handle_bad_chars():
    r = register(handle="bad handle")
    assert r.status_code == 422


def test_register_handle_boundary_ok():
    # 3 and 20 chars are both valid per HANDLE_RE.
    assert register(email="a@test.com", handle="abc").status_code == 201
    assert register(email="b@test.com", handle="a" * 20).status_code == 201


def test_register_short_password():
    r = register(password="short")
    assert r.status_code == 422


def test_register_password_boundary_ok():
    r = register(password="12345678")   # exactly 8 chars
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
    """The role claim in the token must be uppercase (matches UserRole.name
    and _VALID_ROLES in security.py). Regression test for the earlier bug
    where login passed user.role.name.lower()."""
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
    r = client.get("/api/me", headers={"Authorization": "Token abc"})   # not Bearer
    assert r.status_code == 401


def test_me_expired_token():
    expired = jwt.encode(
        {
            "sub": "999",
            "role": "USER",
            "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1),
        },
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )
    r = client.get("/api/me", headers=auth_header(expired))
    assert r.status_code == 401


def test_me_token_for_deleted_user():
    """A valid, unexpired token whose user no longer exists must 401."""
    expired_payload = {
        "sub": "999999",  # nobody has this id
        "role": "USER",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
    }
    token = jwt.encode(expired_payload, os.environ["SECRET_KEY"], algorithm="HS256")
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
    r = client.patch("/api/me/handle", json={"handle": "newhandle"}, headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["handle"] == "newhandle"


def test_change_handle_to_taken():
    register(handle="alice")
    register(email="bob@test.com", handle="bob")
    token = login().json()["access_token"]   # logs in as alice
    r = client.patch("/api/me/handle", json={"handle": "bob"}, headers=auth_header(token))
    assert r.status_code == 409


def test_change_handle_own_capitalization():
    register(handle="myhandle")
    token = login().json()["access_token"]
    r = client.patch("/api/me/handle", json={"handle": "MyHandle"}, headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["handle"] == "MyHandle"


def test_change_handle_requires_auth():
    r = client.patch("/api/me/handle", json={"handle": "newhandle"})
    assert r.status_code == 401


def test_admin_cannot_change_handle():
    token = login_as_admin().json()["access_token"]
    r = client.patch("/api/me/handle", json={"handle": "newhandle"}, headers=auth_header(token))
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
    """After a successful password change, the old password stops working
    and the new one works."""
    register()
    token = login().json()["access_token"]

    r = client.patch("/api/me/password", json={
        "current_password": "password123",
        "new_password": "brandnewpass456",
    }, headers=auth_header(token))
    assert r.status_code == 200

    # Old password no longer valid
    assert login(password="password123").status_code == 401
    # New password works
    assert login(password="brandnewpass456").status_code == 200


def test_admin_cannot_change_password():
    token = login_as_admin().json()["access_token"]
    r = client.patch("/api/me/password", json={
        "current_password": ADMIN_PASSWORD,
        "new_password": "newpassword123",
    }, headers=auth_header(token))
    assert r.status_code == 403