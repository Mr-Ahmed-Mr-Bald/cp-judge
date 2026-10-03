import json
import logging
import os
import select
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select as sa_select, text
from sqlalchemy.orm import Session
import psycopg2
import psycopg2.extensions

from dotenv import load_dotenv
load_dotenv()

from paths import REPO_ROOT, from_repo, problems_dir
from database import (
  Submission,
  SubmissionStatus,
  SubmissionVerdict,
  SessionLocal,
  LISTEN_CHANNEL,
  LISTEN_TIMEOUT
)


JUDGE_PATH = from_repo(os.environ["JUDGE_PATH"])
PROBLEMS_DIR = problems_dir()

if not JUDGE_PATH.is_file():
  raise RuntimeError(
    f"Engine entrypoint not found: {JUDGE_PATH} "
    f"(JUDGE_PATH={os.environ['JUDGE_PATH']!r} resolved from {REPO_ROOT})"
  )
if not PROBLEMS_DIR.is_dir():
  raise RuntimeError(
    f"Problems directory not found: {PROBLEMS_DIR} "
    f"(PROBLEMS_DIR={os.environ.get('PROBLEMS_DIR')!r} resolved from {REPO_ROOT})"
  )

ENGINE_TIMEOUT = int(os.environ.get("ENGINE_TIMEOUT", "300"))
RECONNECT_DELAY = 2.0

# Logging configuration for the root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# Setting sqlalchemy's logging level to WARNING to avoid spamming the output
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Creating a new logger for this module
log = logging.getLogger(__name__)


def recover_stale_submissions():
  db = SessionLocal()
  try:
    stale = db.scalars(
      sa_select(Submission).where(
        Submission.status.in_([
          SubmissionStatus.RUNNING,
          SubmissionStatus.COMPILING
        ])
      )
    ).all()

    for sub in stale:
      sub.status = SubmissionStatus.PENDING
      db.execute(
        text("SELECT pg_notify(:channel, :payload)"),
        {"channel": LISTEN_CHANNEL, "payload": str(sub.id)}
      )
      sub.current_test = None

    db.commit()
  
  finally:
    db.close()

_shutdown_requested = False
_current_proc: subprocess.Popen | None = None
_wakeup_r: socket.socket | None = None
_wakeup_w: socket.socket | None = None

def _wake() -> None:
  """Unblocks the main thread's select() immediately.

  A flag alone cannot do this: the main thread is parked inside select() and a
  signal handler that only sets a boolean is not noticed until select returns on
  its own timeout. With the fallback timeout left long, SIGTERM would stall
  shutdown for that whole timeout, so the handler writes a byte to a self-pipe
  that is in the select set instead.
  """
  if _wakeup_w is None:
    return
  try:
    _wakeup_w.send(b"\x00")
  except OSError:
    pass


def _drain_wakeup() -> None:
  """Empties the self-pipe. Leaving a byte unread would make select() return
  instantly forever."""
  if _wakeup_r is None:
    return
  while True:
    try:
      if not _wakeup_r.recv(4096):
        return
    except OSError:
      return


def _sleep_or_shutdown(delay: float) -> None:
  """Waits, but returns at once if a shutdown signal arrives."""
  if _wakeup_r is None:
    time.sleep(delay)
    return
  select.select([_wakeup_r], [], [], delay)
  _drain_wakeup()


def _handle_sigterm(signum, frame):
  global _shutdown_requested
  log.info("SIGTERM received — shutting down after current job")
  _shutdown_requested = True
  if _current_proc is not None and _current_proc.poll() is None:
    try:
      _current_proc.kill()
    except Exception:
      log.exception("Failed to kill engine subprocess on shutdown")
  _wake()

def claim_next(db: Session) -> int | None:

  sub = db.scalar(
    sa_select(Submission)
    .where(Submission.status == SubmissionStatus.PENDING)
    .order_by(Submission.id)
    .limit(1)
    .with_for_update(skip_locked=True)
  )

  if sub is None:
    return None

  sub.status = SubmissionStatus.COMPILING
  sub_id = sub.id
  db.commit()
  return sub_id


def _kill_after(proc: subprocess.Popen, timeout: int, sub_id: int) -> threading.Timer:
  def killer():
    if proc.poll() is None:
      log.error("[sub %d] engine timed out after %ds — killing", sub_id, timeout)
      try:
        proc.kill()
      except Exception:
        log.exception("[sub %d] failed to kill engine", sub_id)

  t = threading.Timer(timeout, killer)
  t.daemon = True
  t.start()
  return t

def judge(sub_id: int) -> None:
  global _current_proc

  db = SessionLocal()
  try:
    sub = db.get(Submission, sub_id)
    if sub is None:
      log.error("[sub %d] disappeared before judging", sub_id)
      return
    
    problem = sub.problem
    problem_dir = PROBLEMS_DIR / problem.slug
    
    with tempfile.TemporaryDirectory() as tmp:
      tmp_path = Path(tmp)
      solution_file = tmp_path / "solution.cpp"
      solution_file.write_text(sub.source_code, encoding="utf-8")
      stderr_log = tmp_path / "engine_stderr.log"

      log.info("[sub %d] judging (problem=%s)", sub_id, problem.slug)

      with open(stderr_log, "w") as stderr_f:
        proc = subprocess.Popen(
          [
            sys.executable,
            str(JUDGE_PATH),
            "--problem", str(problem_dir),
            "--source", str(solution_file)
          ],
          stdout=subprocess.PIPE,
          stderr=stderr_f,
          text=True
        )
      
        _current_proc = proc
        timer = _kill_after(proc, ENGINE_TIMEOUT, sub.id)

        got_done = False
        try:
          for rline in (proc.stdout if proc.stdout else []):
            line = rline.strip()
            if not line:
              continue
            
            try:
              event = json.loads(line)
            except json.JSONDecodeError:
              log.warning("[sub %d] non-JSON from engine: %r", sub_id, line)
              continue

            etype = event.get("event")
            if etype == "compiling":
              sub.status = SubmissionStatus.COMPILING

            elif etype == "running":
              sub.status = SubmissionStatus.RUNNING
              sub.current_test = event.get("test")

            elif etype == "done":
              sub.status = SubmissionStatus.DONE
              sub.verdict = event.get("verdict", SubmissionVerdict.JE)
              sub.failed_test = event.get("test")
              sub.judged_at = datetime.now(timezone.utc)
              got_done = True

            db.commit()

        except Exception:
          log.exception("[sub %d] error reading engine output", sub_id)
          try:
            proc.kill()
          except:
            pass
        finally:
          timer.cancel()
          try:
            proc.wait(timeout=5)
          except subprocess.TimeoutExpired:
            log.error("[sub %d] engine did not exit after kill", sub_id)
            proc.kill()
            proc.wait()
          
          _current_proc = None

        if not got_done:
          log.error(
            "[sub %d] engine exited without done event (exit=%s)",
            sub_id, proc.returncode,
          )
          if stderr_log.exists():
            log.error("[sub %d] engine stderr:\n%s", sub_id, stderr_log.read_text())
          sub.status = SubmissionStatus.DONE
          sub.verdict = SubmissionVerdict.JE
          sub.current_test = None
          sub.judged_at = datetime.now(timezone.utc)
          db.commit()
  finally:
    db.close()
      

def _drain_queue() -> None:
  """Judges every pending submission until the queue is empty."""
  while not _shutdown_requested:
    db = SessionLocal()
    try:
      sub_id = claim_next(db)
    finally:
      db.close()

    if sub_id is None:
      return

    log.info("[sub %d] claimed", sub_id)
    judge(sub_id)
    log.info("[sub %d] finished", sub_id)


def _open_listener():
  """Opens the dedicated LISTEN connection.

  This connects with psycopg2 directly instead of through SQLAlchemy,
  because it needs psycopg2's raw driver API: set_isolation_level to
  enter autocommit (otherwise notifications stay invisible inside an
  open transaction until it commits) and fileno() so that select() can
  watch the socket. Going through an engine would return whichever
  driver the postgresql:// URL resolves to, and SQLAlchemy 2.1 defaults
  that scheme to psycopg, whose API differs.
  """
  connection = psycopg2.connect(os.environ["DATABASE_URL"])
  connection.set_isolation_level(
    psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
  )
  with connection.cursor() as cursor:
    cursor.execute(f'LISTEN "{LISTEN_CHANNEL}"')
  return connection


def main() -> None:
  global _wakeup_r, _wakeup_w

  log.info("Worker starting up")
  recover_stale_submissions()

  _wakeup_r, _wakeup_w = socket.socketpair()
  _wakeup_r.setblocking(False)
  _wakeup_w.setblocking(False)

  try:
    while not _shutdown_requested:
      try:
        connection = _open_listener()
      except (psycopg2.Error, OSError) as error:
        log.error("could not open listener connection (%s) — retrying", error)
        _sleep_or_shutdown(RECONNECT_DELAY)
        continue

      log.info("Listening on channel %r", LISTEN_CHANNEL)

      try:
        # Anything already queued when we connected was never notified to
        # us, so drain before the first wait.
        _drain_queue()

        while not _shutdown_requested:
          ready, _, _ = select.select(
            [connection, _wakeup_r], [], [], LISTEN_TIMEOUT
          )

          if _wakeup_r in ready:
            _drain_wakeup()

          if connection in ready:
            # The notification is only a doorbell: its payload is not
            # trusted, because NOTIFY is not durable. The table stays
            # the source of truth, and the id is looked up by claiming
            # from it.
            connection.poll()
            connection.notifies.clear()
            _drain_queue()

      except (psycopg2.Error, OSError) as error:
        # A dropped connection leaves the socket readable forever, so
        # this has to be caught and the connection rebuilt. Letting
        # poll() raise psycopg2.OperationalError escape would kill the
        # worker, and swallowing the error without reconnecting would
        # spin on a dead socket.
        log.error("listener connection lost (%s) — reconnecting", error)
        _sleep_or_shutdown(RECONNECT_DELAY)

      finally:
        try:
          connection.close()
        except Exception:
          pass

  finally:
    _wakeup_r.close()
    _wakeup_w.close()

  log.info("Worker stopped")


if __name__ == "__main__":
  signal.signal(signal.SIGTERM, _handle_sigterm)
  try:
    main()
  except KeyboardInterrupt:
    log.info("Interrupted, shutting down")