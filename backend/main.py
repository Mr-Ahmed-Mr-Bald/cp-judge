import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

load_dotenv()

from database import Problem, get_db # noqa: E402
from schemas import ProblemDetail, ProblemListItem # noqa: E402

PROBLEMS_DIR = Path(
  os.getenv("PROBLEMS_DIR", Path(__file__).parent.parent / "engine" / "problems")
).resolve()

app = FastAPI(description="Competitive Programming Judge API")

@app.get("/api/problems", response_model=list[ProblemListItem])
def list_problems(db: Session = Depends(get_db)):
  problems = db.scalars(select(Problem)).all()
  return problems

@app.get("/api/problems/{slug}", response_model=ProblemDetail)
def get_problem(slug: str, db: Session = Depends(get_db)):
  problem = db.scalar(select(Problem).where(Problem.slug == slug))

  if problem is None:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Problem '{slug}' not found"
    )
  
  statement_path = PROBLEMS_DIR / slug / "statement.md"
  if not statement_path.exists():
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Problem statement for '{slug}' not found"
    )
  
  return {
    "id": problem.id,
    "slug": problem.slug,
    "title": problem.title,
    "time_limit_ms": problem.time_limit_ms,
    "memory_limit_mb": problem.memory_limit_mb,
    "created_at": problem.created_at,
    "test_count": problem.test_count,
    "tags": problem.tags,
    "statement_md": statement_path.read_text(encoding="utf-8")
  }