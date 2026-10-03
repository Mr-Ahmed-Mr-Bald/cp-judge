import os
from typing import Optional, Text
from enum import Enum as PyEnum, auto
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import String, DateTime, ForeignKey, func, Enum as SaEnum, create_engine, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, relationship

load_dotenv()
DATABASE_URL = os.getenv(key="DATABASE_URL", default="postgresql://postgres:postgres@localhost:5432/cp_judge_db")

engine = create_engine(url=DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

# The worker opens its own dedicated connection to LISTEN on, using
# psycopg2 directly (worker._open_listener). It deliberately bypasses
# SQLAlchemy: the raw driver APIs it needs -- set_isolation_level,
# poll, fileno -- are psycopg2's, and going through the ORM would hand
# back whichever driver the postgresql:// URL happens to resolve to
# (SQLAlchemy 2.1 defaults that scheme to psycopg, which does not have
# the same API).
LISTEN_CHANNEL = "new_submission"
# Fallback poll, not the normal path: a notification normally wakes the
# worker at once. This only bounds how long a missed notification goes
# unnoticed.
LISTEN_TIMEOUT = 20.0

class UserRole(PyEnum):
  USER = auto()
  ADMIN = auto()

class Base(DeclarativeBase):
  pass

class User(Base):
  __tablename__ = "users"

  id: Mapped[int] = mapped_column(primary_key=True)
  handle: Mapped[str] = mapped_column(type_=String(255))
  handle_lower: Mapped[str] = mapped_column(type_=String(255), unique=True, index=True)
  email: Mapped[str] = mapped_column(type_=String(255), unique=True)
  role: Mapped[UserRole] = mapped_column(type_=SaEnum(UserRole, name="user_role_enum"), default=UserRole.USER)
  password_hash: Mapped[str] = mapped_column(type_=String(255))
  created_at: Mapped[datetime] = mapped_column(type_=DateTime(timezone=True), server_default=func.now())

class Problem(Base):
  __tablename__ = "problems"

  id: Mapped[int] = mapped_column(primary_key=True)
  slug: Mapped[str] = mapped_column(type_=String(255), unique=True, index=True)
  title: Mapped[str] = mapped_column(type_=String(255))
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  time_limit_ms: Mapped[int]
  memory_limit_mb: Mapped[int]
  test_count: Mapped[int] = mapped_column(default=0, server_default="0")

  tags: Mapped[list["Tag"]] = relationship(
    secondary="problem_tags",
    back_populates="problems",
    lazy="selectin",
    passive_deletes=True
  )

class Tag(Base):
  __tablename__ = "tags"

  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(type_=String(255), unique=True)

  problems: Mapped[list["Problem"]] = relationship(
    secondary="problem_tags",
    back_populates="tags",
    lazy="selectin",
    passive_deletes=True
  )

class ProblemTag(Base):
  __tablename__ = "problem_tags"

  problem_id: Mapped[int] = mapped_column(ForeignKey(column="problems.id", ondelete="CASCADE"), primary_key=True)
  tag_id: Mapped[int] = mapped_column(ForeignKey(column="tags.id", ondelete="CASCADE"), primary_key=True)

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

class SubmissionStatus(str, PyEnum):
  PENDING = "PENDING"
  COMPILING = "COMPILING"
  RUNNING = "RUNNING"
  DONE = "DONE"

class SubmissionVerdict(str, PyEnum):
  AC = "AC"
  WA = "WA"
  TL = "TL"
  ML = "ML"
  RE = "RE"
  CE = "CE"
  JE = "JE"

class Submission(Base):
  __tablename__ = "submissions"

  id: Mapped[int] = mapped_column(primary_key=True)
  user_id: Mapped[int] = mapped_column(ForeignKey(column="users.id", ondelete="CASCADE"))
  problem_id: Mapped[int] = mapped_column(ForeignKey(column="problems.id", ondelete="CASCADE"))
  source_code: Mapped[str]

  status: Mapped[SubmissionStatus] = mapped_column(
    type_=SaEnum(SubmissionStatus, name="submission_status_enum"),
    server_default=SubmissionStatus.PENDING,
    index=True
  )
  verdict: Mapped[Optional[SubmissionVerdict]] = mapped_column(
    type_=SaEnum(SubmissionVerdict, name="submission_verdict_enum"),
    nullable=True
  )

  failed_test: Mapped[Optional[int]] = mapped_column(nullable=True)
  current_test: Mapped[Optional[int]] = mapped_column(nullable=True)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  judged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

  user: Mapped["User"] = relationship("User", lazy="select")
  problem: Mapped["Problem"] = relationship("Problem", lazy="select")

Index("ix_submissions_status_id", Submission.status, Submission.id)