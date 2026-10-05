import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import jwt

load_dotenv()

from database import User, UserRole, Problem, get_db, SessionLocal, Submission, SubmissionStatus
from schemas import (
    RegisterRequest, LoginRequest, ChangeHandleRequest, ChangePasswordRequest,
    UserOut, TokenResponse, ProblemListItem, ProblemDetail, SubmissionRequest,
    SubmissionListItem, SubmissionOut
)
from security import (
    hash_password, verify_password, create_access_token, decode_access_token,
)
from paths import problems_dir, REPO_ROOT
from settings import LISTEN_CHANNEL

sys.path.insert(0, str(REPO_ROOT))

# E402: import after the sys.path bootstrap above, which is what makes
# `engine` importable at all.
from engine.package_spec import STATEMENT_MD  # noqa: E402

PROBLEMS_DIR = problems_dir()

# Admin seeding at startup
def seed_admin() -> None:
  admin_email = os.getenv("ADMIN_EMAIL")
  admin_handle = os.getenv("ADMIN_HANDLE")
  admin_password = os.getenv("ADMIN_PASSWORD")

  if not all([admin_email, admin_handle, admin_password]):
    raise RuntimeError("ADMIN_EMAIL, ADMIN_HANDLE, ADMIN_PASSWORD must all be set")

  db = SessionLocal()
  try:
    existing = db.scalar(select(User).where(User.role == UserRole.ADMIN))
    if existing is not None:
      return
    
    db.add(User(
      email=admin_email.lower(), # type: ignore
      handle=admin_handle,
      handle_lower=admin_handle.lower(), # type: ignore
      password_hash=hash_password(admin_password), # type: ignore
      role=UserRole.ADMIN
    ))

    try:
      db.commit()
    except IntegrityError:
      db.rollback()
  finally:
    db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
  seed_admin()
  yield

app = FastAPI(description="Competitive Programming Judge API", lifespan=lifespan)


# Authentication dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def get_current_user(
  token: str = Depends(oauth2_scheme),
  db: Session = Depends(get_db)
) -> User:

  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"}
  )
  try:
    payload = decode_access_token(token)
    user_id = int(payload["sub"])
  except (jwt.InvalidTokenError, KeyError, ValueError):
    raise credentials_exception

  user = db.get(User, user_id)
  if user is None:
    raise credentials_exception
  
  return user

def require_not_admin(current_user: User = Depends(get_current_user)) -> User:
  if current_user.role == UserRole.ADMIN:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Admin account cannot be modified"
    )
  return current_user

# Authentication endponits  
@app.post("/api/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
  user = User(
    email=req.email.lower(),
    handle=req.handle,
    handle_lower=req.handle.lower(),
    password_hash=hash_password(req.password),
    role=UserRole.USER
  )

  try:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
  except IntegrityError as e:
    db.rollback()

    err = str(e.orig).lower()
    if "email" in err:
      detail = "Email already registered"
    elif "handle" in err:
      detail = "Handle already taken"
    else:
      detail="Duplicate value"
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

@app.post("/api/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):

  invalid = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid email or password"
  )

  user = db.scalar(select(User).where(User.email == req.email.lower()))

  if user is None:
    raise invalid

  if not verify_password(user.password_hash, req.password):
    raise invalid

  token = create_access_token(user_id=user.id, role=user.role.name)
  return TokenResponse(access_token=token)

@app.get("/api/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
  return current_user

@app.patch("/api/me/handle", response_model=UserOut)
def change_handle(
  req: ChangeHandleRequest,
  db: Session = Depends(get_db),
  current_user: User = Depends(require_not_admin)
):

  new_handle_lower = req.handle.lower()
  current_user.handle = req.handle

  if new_handle_lower != current_user.handle_lower:
    current_user.handle_lower = new_handle_lower

  try:
    db.commit()
  except IntegrityError:
    db.rollback()
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="Handle already taken"
    ) from None
  
  db.refresh(current_user)
  return current_user

@app.patch("/api/me/password", response_model=UserOut)
def change_password(
  req: ChangePasswordRequest,
  db: Session = Depends(get_db),
  current_user: User = Depends(require_not_admin)
):
  if not verify_password(current_user.password_hash, req.current_password):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Current password is not correct"
    )

  current_user.password_hash = hash_password(req.new_password)
  db.commit()
  db.refresh(current_user)
  return current_user

# Problems endpoints
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
  
  statement_path = PROBLEMS_DIR / slug / STATEMENT_MD
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

MAX_PENDING_PER_USER = 5
MAX_PENDING_GLOBAL = 100

@app.post("/api/problems/{slug}/submissions",
  response_model=SubmissionOut,
  status_code=status.HTTP_201_CREATED)
def submit(
  slug: str,
  req: SubmissionRequest, 
  db: Session = Depends(get_db), 
  current_user: User = Depends(get_current_user)
):
  problem = db.scalar(select(Problem).where(Problem.slug == slug))
  if problem is None:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Problem '{slug}' not found"
    )

  pending_count_global = db.execute(
    select(func.count(Submission.id))
    .where(Submission.status == SubmissionStatus.PENDING)
  ).scalar_one()

  if pending_count_global >= MAX_PENDING_GLOBAL:
    raise HTTPException(
      status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
      detail="Server is busy. Try again later"
    )

  pending_count_for_user = db.execute(
    select(func.count(Submission.id)).where(
      Submission.user_id == current_user.id,
      Submission.status == SubmissionStatus.PENDING
    )
  ).scalar_one()

  if pending_count_for_user >= MAX_PENDING_PER_USER:
    raise HTTPException(
      status_code=status.HTTP_429_TOO_MANY_REQUESTS,
      detail="Too many pending submissions"
    )

  submission = Submission(
    user_id=current_user.id,
    problem_id=problem.id,
    source_code=req.source_code,
    status=SubmissionStatus.PENDING
  )

  # The row and the wakeup are committed together on purpose. pg_notify is
  # transactional — the notification is delivered at COMMIT — so putting the
  # INSERT and the NOTIFY in one transaction makes the pair atomic. Committing
  # the row first and notifying in a second transaction would leave a window in
  # which a crash strands a committed submission that no worker is woken for,
  # recoverable only by the worker's fallback poll.
  db.add(submission)
  db.execute(
    text("SELECT pg_notify(:channel, :payload)"),
    {"channel": LISTEN_CHANNEL, "payload": str(submission.id)}
  )
  db.commit()
  return serialize_submission(submission)

def serialize_submission(submission: Submission) -> dict:
  return {
    "id": submission.id,
    "problem_id": submission.problem_id,
    "problem_slug": submission.problem.slug,
    "problem_title": submission.problem.title,
    "status": submission.status,
    "source_code": submission.source_code,
    "created_at": submission.created_at,
    "verdict": submission.verdict,
    "current_test": submission.current_test,
    "failed_test": submission.failed_test,
    "judged_at": submission.judged_at,
  }

@app.get("/api/submissions/{sub_id}",
  response_model=SubmissionOut)
def get_submission(
  sub_id: int, 
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  submission = db.get(Submission, sub_id)
  if submission is None or submission.user_id != current_user.id:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
  return serialize_submission(submission)

@app.get("/api/submissions", response_model=list[SubmissionListItem])
def list_submissions(
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
  problem_slug: Optional[str] = None,
  limit: Optional[int] = 20
):
  if problem_slug is not None:
    problem_exists = db.scalar(
      select(Problem.id).where(Problem.slug == problem_slug)
    )
    if problem_exists is None:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Problem '{problem_slug}' not found"
      )

  stmt = (
    select(Submission, Problem.slug, Problem.title)
    .join(Problem, Submission.problem_id == Problem.id)
    .where(Submission.user_id == current_user.id)
    .order_by(Submission.id.desc())
    .limit(limit)
  )

  if problem_slug is not None:
    stmt = stmt.where(Problem.slug == problem_slug)

  return [
    SubmissionListItem(
      id=submission.id,
      problem_id=submission.problem_id,
      problem_slug=slug,
      problem_title=title,
      status=submission.status,
      created_at=submission.created_at,
      verdict=submission.verdict,
      failed_test=submission.failed_test,
      judged_at=submission.judged_at,
    )
    for submission, slug, title in db.execute(stmt).all()
  ]

  