import os
from enum import Enum as PyEnum, auto
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import String, DateTime, ForeignKey, func, Enum as SaEnum, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, relationship

load_dotenv()
DATABASE_URL = os.getenv(key="DATABASE_URL", default="postgresql://postgres:postgres@localhost:5432/cp_judge_db")

engine = create_engine(url=DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

class UserRole(PyEnum):
  USER = auto()
  ADMIN = auto()

class Base(DeclarativeBase):
  pass

class User(Base):
  __tablename__ = "users"

  id: Mapped[int] = mapped_column(primary_key=True)
  handle: Mapped[str] = mapped_column(type_=String(255), unique=True, index=True)
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
    back_populates="problems"
  )

class Tag(Base):
  __tablename__ = "tags"

  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(type_=String(255), unique=True)

  problems: Mapped[list["Problem"]] = relationship(
    secondary="problem_tags",
    back_populates="tags"
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