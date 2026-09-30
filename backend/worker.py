import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from dotenv import load_dotenv

load_dotenv()

from database import (
    Problem,
    Submission,
    SubmissionStatus,
    SubmissionVerdict,
    SessionLocal
)

from paths import REPO_ROOT, from_repo, problems_dir

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
SLEEP_INTERVAL = 0.5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

def recover_stale_submissions():
  db = SessionLocal()
  try:
    stale = db.scalars(
      select(Submission).where(
        Submission.status.in_(
          [SubmissionStatus.RUNNING,
          SubmissionStatus.COMPILING]
        )
      )
    ).all()

    for sub in stale:
      sub.status = SubmissionStatus.PENDING
      sub.current_test = None

    db.commit()
  
  finally:
    db.close()

_shutdown_requested = False
_current_proc: subprocess.Popen | None = None


def _handle_sigterm(signum, frame):
  global _shutdown_requested
  log.info("SIGTERM received — shutting down after current job")
  _shutdown_requested = True
  if _current_proc is not None and _current_proc.poll() is None:
    try:
      _current_proc.kill()
    except Exception:
      log.exception("Failed to kill engine subprocess on shutdown")

def claim_next(db: Session) -> int | None:

  sub = db.scalar(
    select(Submission)
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
      

def main() -> None:
  log.info("Worker starting up")
  recover_stale_submissions()

  while not _shutdown_requested:
    db = SessionLocal()
    try:
      sub_id = claim_next(db)
    finally:
      db.close()

    if sub_id is None:
      time.sleep(SLEEP_INTERVAL)
      continue

    log.info("[sub %d] claimed", sub_id)
    judge(sub_id)
    log.info("[sub %d] finished", sub_id)

  log.info("Worker stopped")


if __name__ == "__main__":
  signal.signal(signal.SIGTERM, _handle_sigterm)
  try:
    main()
  except KeyboardInterrupt:
    log.info("Interrupted, shutting down")