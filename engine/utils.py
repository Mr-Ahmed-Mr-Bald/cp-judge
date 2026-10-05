import sys
from typing import NoReturn

def fail(msg: str) -> NoReturn:
  """Prints error message, and terminates with exit code 1"""
  print(f"Error: {msg}", file=sys.stderr)
  sys.exit(1)
