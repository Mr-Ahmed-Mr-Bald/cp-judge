import os
import logging
import datetime
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
import jwt

logger = logging.getLogger(__name__)

_SECRET_KEY = os.getenv("SECRET_KEY")
_ALGORITHM = os.getenv("ALGORITHM", "HS256")
_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))

if not _SECRET_KEY:
  raise RuntimeError("SECRET_KEY environment variable is not set")

_VALID_ROLES = frozenset({"USER", "ADMIN"})

_ph = PasswordHasher()

def hash_password(plaintext: str) -> str:
  return _ph.hash(plaintext)

def verify_password(stored_hash: str, plaintext: str) -> bool:
  try:
    _ph.verify(stored_hash, plaintext)
    return True
  except VerifyMismatchError:
    return False
  except (VerificationError, InvalidHashError):
    logger.exception("Invalid password hash encountered during verification.")
    return False

def create_access_token(user_id: int, role: str) -> str:
  if role not in _VALID_ROLES:
    raise ValueError(f"Invalid role: must be one of {sorted(_VALID_ROLES)}")

  now = datetime.datetime.now(datetime.timezone.utc) 
  payload = {
    "sub": str(user_id),
    "role": role,
    "exp": now + datetime.timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
  }

  return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)

def decode_access_token(token: str) -> dict:
  return jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])