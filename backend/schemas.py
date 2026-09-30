import re
from enum import Enum
from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    field_validator,
)

class ProblemListItem(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  slug: str
  title: str
  time_limit_ms: int
  memory_limit_mb: int
  tags: list[str]

  @field_validator("tags", mode="before")
  @classmethod
  def flatten_tags(cls, v):
    try:
      return [t.name for t in v]
    except (AttributeError, TypeError) as e:
      raise ValueError(f"Expected a list of tag objects. Got {v}") from e


class ProblemDetail(ProblemListItem):
  test_count: int
  statement_md: str

class TagOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)
  name: str

HANDLE_RE = re.compile(r"[A-Za-z0-9_]{3,20}$")
MIN_PASSWORD_LEN = 8
MAX_PASSWORD_LEN = 256

def _check_handle(v: str) -> str:
  if not HANDLE_RE.fullmatch(v):
    raise ValueError("handle must be 3–20 characters: A-Z a-z 0-9 _")
  return v

def _check_password(v: str) -> str:
  if len(v) < MIN_PASSWORD_LEN:
    raise ValueError(f"password must be at least {MIN_PASSWORD_LEN} characters")
  if len(v) > MAX_PASSWORD_LEN:
    raise ValueError(f"password must be at most {MAX_PASSWORD_LEN} characters")
  return v


Handle = Annotated[str, AfterValidator(_check_handle)]
Password = Annotated[str, AfterValidator(_check_password)]

class RegisterRequest(BaseModel):
  email: EmailStr
  handle: Handle
  password: Password

class LoginRequest(BaseModel):
  email: EmailStr
  password: Password

class ChangeHandleRequest(BaseModel):
  handle: Handle

class ChangePasswordRequest(BaseModel):
  current_password: Password
  new_password: Password

class UserOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  email: str
  handle: str
  role: Literal["USER", "ADMIN"]
  created_at: datetime

  @field_validator("role", mode="before")
  @classmethod
  def serialize_role(clas, v):
    if isinstance(v, Enum):
      return v.name
    return v

class TokenResponse(BaseModel):
  access_token: str
  token_type: str = "bearer"


SOURCE_MAX_BYTES = 64 * 1024
class SubmissionRequest(BaseModel):
  source_code: str

  @field_validator("source_code")
  @classmethod
  def check_size(cls, v: str) -> str:
    if (len(v.encode("utf-8")) > SOURCE_MAX_BYTES):
      raise ValueError("source code exceeds 64 KiB")
    return v

class SubmissionListItem(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  problem_id: int
  problem_slug: str
  problem_title: str
  status: str
  created_at: datetime
  verdict: Optional[str] = None
  failed_test: Optional[int] = None
  judged_at: Optional[datetime] = None

  @field_validator("status", "verdict", mode="before")
  @classmethod
  def enum_to_str(cls, v):
    if hasattr(v, "value"):
      return v.value
    return v

class SubmissionOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  problem_id: int
  problem_slug: str
  problem_title: str
  status: str
  source_code: str
  created_at: datetime
  verdict: Optional[str] = None
  current_test: Optional[int] = None
  failed_test: Optional[int] = None
  judged_at: Optional[datetime] = None

  @field_validator("status", "verdict", mode="before")
  @classmethod
  def enum_to_str(cls, v):
    if hasattr(v, "value"):
      return v.value
    return v