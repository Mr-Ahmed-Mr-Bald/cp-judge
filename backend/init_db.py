import os
import json
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.orm import Session
load_dotenv()

from database import (
  Base,
  Problem,
  Tag,
  User,
  UserRole,
  SessionLocal,
  engine
)


ADMIN_EMAIL = "admin@judge.local"
PROBLEMS_DIR = Path(
  os.getenv("PROBLEMS_DIR", Path(__file__).parent.parent / "engine" / "problems")
).resolve()

def seed_admin(db: Session):
  admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
  if admin is not None:
    return
  db.add(User(
    handle="admin",
    email=ADMIN_EMAIL,
    password_hash="admin", # will add hashing later
    role=UserRole.ADMIN
  ))

def get_or_create_tag(db: Session, name: str) -> Tag:
  tag = db.query(Tag).filter(Tag.name == name).first()
  if tag is None:
    tag = Tag(name=name)
    db.add(tag)
    db.flush()
  return tag

def seed_problems(db: Session):
  if not PROBLEMS_DIR.exists():
    raise RuntimeError(f"Problems directory does not exist: {PROBLEMS_DIR}")
  
  for problem_folder in sorted(PROBLEMS_DIR.iterdir()):
    if not problem_folder.is_dir():
      continue
    
    slug = problem_folder.name
    config_file = problem_folder / "config.json"

    if not config_file.exists():
      raise RuntimeError(f"config.json file does not exist: {problem_folder}")
    
    with open(config_file, "r", encoding="utf-8") as f:
      config = json.load(f)

    tests_dir = problem_folder / "tests"
    test_count = sum(
      1 for p in tests_dir.glob(r"*.in")
    )

    tag_names = config.get("tags", [])
    tags = [get_or_create_tag(db, name) for name in tag_names]

    if db.query(Problem).filter(Problem.slug == slug).first() is None:
      db.add(Problem(
        slug=slug,
        title=config["title"],
        time_limit_ms=config["time_limit"],
        memory_limit_mb=config["memory_limit"],
        test_count=test_count,
        tags=tags
      ))


def init_db():
  print("Creating database tables...")
  db = SessionLocal()
  Base.metadata.create_all(bind=engine)

  try:
    seed_admin(db)
    seed_problems(db)
    db.commit()
    print("Database initialization complete.")
  except Exception:
    db.rollback()
    raise
  finally:
    db.close()

if __name__ == "__main__":
  init_db()