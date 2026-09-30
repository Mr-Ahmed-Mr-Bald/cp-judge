import os
from pathlib import Path

# backend/ -> repo root
REPO_ROOT = Path(__file__).resolve().parent.parent


def from_repo(value: str) -> Path:
  """Resolve a path from .env against the repo root rather than the CWD.

  Values in backend/.env are written relative to the repo root, but the API,
  the seeder and the worker are all started from different working
  directories. Resolving them against os.getcwd() silently produces
  nonexistent paths, which is how a missing engine turned into a silent
  "JE" verdict for every submission.
  """
  path = Path(value)
  return (path if path.is_absolute() else REPO_ROOT / path).resolve()


def problems_dir() -> Path:
  return from_repo(os.getenv("PROBLEMS_DIR", "engine/problems"))
