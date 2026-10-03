"""
Shared test fixtures for the whole suite.

IMPORTANT: pytest imports every test module before running any test. If
individual test files set os.environ[...] or app.dependency_overrides[get_db]
at module level, the LAST-imported file wins for the whole session, and the
earlier files' tests silently run against the wrong database.

All shared setup — env vars, DB engine, dependency override, per-test
schema/admin/problem seeding — lives here. Test files must NOT set any of
these themselves.
"""
import os

# Set env BEFORE importing any app module.
# security.py reads SECRET_KEY at import time; database.py reads DATABASE_URL.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32b")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.com")
os.environ.setdefault("ADMIN_HANDLE", "testadmin")
os.environ.setdefault("ADMIN_PASSWORD", "adminpassword123")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import (
    Base,
    User,
    UserRole,
    Problem,
    Submission,
    SubmissionStatus,
    get_db,
)
from main import app
from security import hash_password

ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_HANDLE = os.environ["ADMIN_HANDLE"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]

# One shared in-memory SQLite DB for the whole session.
# StaticPool makes every connection see the SAME in-memory database; without
# it, each new connection gets its own fresh empty DB.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


@event.listens_for(engine, "connect")
def _stub_pg_notify(dbapi_connection, connection_record):
    """Stubs pg_notify, which SQLite does not have.

    Submitting wakes the worker with pg_notify, and that only makes sense on
    PostgreSQL. The notification is a doorbell, not the source of truth — the
    submissions row is what the worker claims from — so on SQLite the correct
    behaviour for the call is to do nothing at all. Stubbing it here keeps the
    dialect check out of the request path in main.py.
    """
    dbapi_connection.create_function(
        "pg_notify", 2, lambda channel, payload: None
    )


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Installed ONCE, for the whole session. Never touch this from a test file.
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Fresh schema + admin + one test problem before each test."""
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
        db.add(Problem(
            slug="test-problem",
            title="Test Problem",
            time_limit_ms=1000,
            memory_limit_mb=256,
            test_count=1,
        ))
        db.commit()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db():
    """The session factory bound to the shared test DB.

    Tests that need to monkeypatch worker.SessionLocal (or otherwise hand
    a session factory around) should take this fixture rather than
    importing TestSessionLocal from conftest.
    """
    return TestSessionLocal