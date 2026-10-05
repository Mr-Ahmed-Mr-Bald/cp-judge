import json
from enum import Enum
from typing_extensions import Unpack, TypedDict

class EventType(str, Enum):
  COMPILING= "compiling"
  RUNNING = "running"
  DONE = "done"

class Verdict(str, Enum):
  AC = "AC" # Accepted
  WA = "WA" # Wrong Answer
  TL = "TL" # Time Limit Exceeded
  ML = "ML" # Memory Limit Exceeded
  RE = "RE" # Runtime Error
  CE = "CE" # Compile Error
  JE = "JE" # Internal Engine Error

class EventFields(TypedDict, total=False):
  verdict: Verdict
  test: int
  message: str

def emit_event(event: EventType, **fields: Unpack[EventFields]) -> None:
  """Emits a JSON event line to stdout and flushes immediately.
  """
  data = {"event": event, **fields}
  print(json.dumps(data), flush=True)