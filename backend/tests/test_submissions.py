"""
Submission + worker tests.

Shared DB, dependency override, and per-test seeding live in
tests/conftest.py. Do not add module-level env vars or engine setup here.

Requires tests/engines/fake_ok.py — a small script that emits the expected
JSON event stream on stdout (compiling / running / done with verdict AC).

Run with: pytest tests/test_submissions.py -v
"""
import os
from pathlib import Path

from fastapi.testclient import TestClient

from database import Submission, SubmissionStatus
from main import app

ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]

SMALL_SOURCE = "#include<bits/stdc++.h>\nint main(){}"
BIG_SOURCE = "x" * (64 * 1024 + 1)

client = TestClient(app, raise_server_exceptions=False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def register_and_login(email="user@test.com", handle="testuser", password="password123"):
    client.post("/api/register", json={
        "email": email, "handle": handle, "password": password,
    })
    r = client.post("/api/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── Submit endpoint ───────────────────────────────────────────────────────────

def test_submit_unauthenticated():
    r = client.post("/api/problems/test-problem/submissions",
                    json={"source_code": SMALL_SOURCE})
    assert r.status_code == 401


def test_submit_unknown_slug():
    token = register_and_login()
    r = client.post("/api/problems/no-such-problem/submissions",
                    json={"source_code": SMALL_SOURCE}, headers=auth(token))
    assert r.status_code == 404


def test_submit_oversized_source():
    token = register_and_login()
    r = client.post("/api/problems/test-problem/submissions",
                    json={"source_code": BIG_SOURCE}, headers=auth(token))
    assert r.status_code in (413, 422)


def test_submit_success():
    token = register_and_login()
    r = client.post("/api/problems/test-problem/submissions",
                    json={"source_code": SMALL_SOURCE}, headers=auth(token))
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "PENDING"
    assert "id" in body
    assert body["source_code"] == SMALL_SOURCE


# ── Get submission ────────────────────────────────────────────────────────────

def test_get_own_submission():
    token = register_and_login()
    sub_id = client.post("/api/problems/test-problem/submissions",
                         json={"source_code": SMALL_SOURCE},
                         headers=auth(token)).json()["id"]
    r = client.get(f"/api/submissions/{sub_id}", headers=auth(token))
    assert r.status_code == 200


def test_get_other_users_submission_returns_404():
    token_a = register_and_login(email="a@test.com", handle="usera")
    token_b = register_and_login(email="b@test.com", handle="userb")
    sub_id = client.post("/api/problems/test-problem/submissions",
                         json={"source_code": SMALL_SOURCE},
                         headers=auth(token_a)).json()["id"]
    r = client.get(f"/api/submissions/{sub_id}", headers=auth(token_b))
    assert r.status_code == 404


def test_get_submission_unauthenticated():
    token = register_and_login()
    sub_id = client.post("/api/problems/test-problem/submissions",
                         json={"source_code": SMALL_SOURCE},
                         headers=auth(token)).json()["id"]
    r = client.get(f"/api/submissions/{sub_id}")
    assert r.status_code == 401


# ── List submissions ──────────────────────────────────────────────────────────

def test_list_submissions_only_own():
    token_a = register_and_login(email="a@test.com", handle="usera")
    token_b = register_and_login(email="b@test.com", handle="userb")
    client.post("/api/problems/test-problem/submissions",
                json={"source_code": SMALL_SOURCE}, headers=auth(token_a))
    client.post("/api/problems/test-problem/submissions",
                json={"source_code": SMALL_SOURCE}, headers=auth(token_a))
    client.post("/api/problems/test-problem/submissions",
                json={"source_code": SMALL_SOURCE}, headers=auth(token_b))

    r = client.get("/api/submissions", headers=auth(token_a))
    assert r.status_code == 200
    assert len(r.json()) == 2


# ── Worker tests ──────────────────────────────────────────────────────────────

def test_worker_normal_run(tmp_path, monkeypatch, test_db):
    import worker

    # Point the worker's session factory at the shared test DB.
    monkeypatch.setattr(worker, "SessionLocal", test_db)

    # Seed a submission directly.
    db = test_db()
    sub = Submission(
        user_id=1, problem_id=1,
        source_code=SMALL_SOURCE,
        status=SubmissionStatus.PENDING,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    sub_id = sub.id
    db.close()

    # Point the worker at the fake engine that always reports AC.
    fake_engine = Path(__file__).parent / "engines" / "fake_ok.py"
    monkeypatch.setattr(worker, "JUDGE_PATH", fake_engine)

    worker.judge(sub_id)

    db = test_db()
    result = db.get(Submission, sub_id)
    assert result.status.value == "DONE"
    assert result.verdict.value == "AC"
    db.close()


def test_worker_recovery(test_db, monkeypatch):
    import worker

    # Seed one COMPILING and one RUNNING submission.
    db = test_db()
    sub1 = Submission(user_id=1, problem_id=1, source_code="x",
                      status=SubmissionStatus.COMPILING)
    sub2 = Submission(user_id=1, problem_id=1, source_code="y",
                      status=SubmissionStatus.RUNNING, current_test=3)
    db.add_all([sub1, sub2])
    db.commit()
    db.refresh(sub1)
    db.refresh(sub2)
    ids = (sub1.id, sub2.id)
    db.close()

    monkeypatch.setattr(worker, "SessionLocal", test_db)
    worker.recover_stale_submissions()

    db = test_db()
    for sid in ids:
        s = db.get(Submission, sid)
        assert s.status == SubmissionStatus.PENDING
        assert s.current_test is None
    db.close()