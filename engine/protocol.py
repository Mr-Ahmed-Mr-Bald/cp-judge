import json
from enum import Enum

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

def emit_event(event_data: dict) -> None:
  """Emits a JSON event line to stdout and flushes immediately.
  """
  print(json.dumps(event_data), flush=True)