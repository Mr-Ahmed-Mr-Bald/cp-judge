import sys
import os
import json
import argparse
import tempfile
from enum import Enum
from pathlib import Path
from typing import Tuple

from compiler import Compiler
from runner import Runner
from checker import Checker

class EventType(str, Enum):
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

def validate_problem_package(problem_path: Path) -> Tuple[bool, str]:
  """Ensures the problem directory is valid before starting execution."""
  
  for path, name in [
    (problem_path, "Problem folder"),
    (problem_path / "tests", "Tests folder"),
    (problem_path / "checker.cpp", "checker.cpp"),
    (problem_path / "config.json", "config.json"),
  ]:
    if not path.exists():
      return (False, f"{name} not found")
  
  return True, ""

def emit_event(event_data: dict) -> None:
  """Emits a JSON event line to stdout and flushes immediately.
  """
  print(json.dumps(event_data))
  sys.stdout.flush()

def main():
  # Set up the argument parser
  parser = argparse.ArgumentParser(description="CP Judge Engine")

  # Define the arguments
  parser.add_argument("--problem", type=Path, required=True, help="Path to problem folder")
  parser.add_argument("--source", type=Path, required=True, help="Path to user's solution")

  # Parse the arguments
  args = parser.parse_args()

  problem_path: Path = args.problem.resolve()
  source_path: Path = args.source.resolve()

  ok, error_message = validate_problem_package(problem_path)
  if (not ok):
    emit_event({
      "event": EventType.DONE,
      "verdict": Verdict.JE,
      "message": error_message
    })
    sys.exit(1)

  if (not source_path.exists() or not source_path.is_file()):
    emit_event({
      "event": EventType.DONE,
      "verdict": Verdict.JE,
      "message": f"Source file not found: {source_path}"
    })
    sys.exit(1)

  config_path = problem_path / "config.json"
  with open(config_path, "r", encoding="utf-8") as f:
    problem_config = json.load(f)

  with tempfile.TemporaryDirectory() as tmp_dir:
    work_dir = Path(tmp_dir)
    user_binary = work_dir / "user_binary"
    checker_binary = work_dir / "checker_binary"

    error_message, success = Compiler.compile(source_path, user_binary)
    if (not success):
      emit_event({
        "event": EventType.DONE,
        "verdict": Verdict.CE,
        "message": error_message
      })
      sys.exit(0)

    checker_source = problem_path / "checker.cpp"
    error_message, success = Compiler.compile(checker_source, checker_binary)
    if (not success):
      emit_event({
        "event": EventType.DONE,
        "verdict": Verdict.JE,
        "message": error_message
      })
      sys.exit(1)

    tests_dir = problem_path / "tests"
    test_files = sorted(list(tests_dir.glob("*.in")))
    for test_idx, test_file in enumerate(test_files):
      ans_file = test_file.with_suffix(".ans")
      if (not ans_file.exists()):
        emit_event({
          "event": EventType.DONE,
          "verdict": Verdict.JE,
          "test": test_idx,
          "message": "Answer file does not exist"
        })
        sys.exit(1)
      
      emit_event({"event": EventType.RUNNING, "test": test_idx})

      pstdout, exit_code, timed_out = Runner.run(
        user_binary, test_file, problem_config["time_limit"], problem_config["memory_limit"]
      )

      if (timed_out):
        emit_event({
          "event": EventType.DONE, 
          "verdict": Verdict.TL,
          "test": test_idx
        })
        sys.exit(0)

      if (exit_code != 0):
        emit_event({
          "event": EventType.DONE, 
          "verdict": Verdict.RE,
          "test": test_idx
        })
        sys.exit(0)

      # Save program stdout to temporary file for checker
      out_file = work_dir / "out.out"
      out_file.write_text(pstdout, encoding="utf-8")

      feedback, is_correct = Checker.check(checker_binary, test_file, out_file, ans_file)
      if (not is_correct):
        emit_event({
          "event": EventType.DONE, 
          "verdict": Verdict.WA,
          "test": test_idx,
          "message": feedback
        })
        sys.exit(0)

    emit_event({"event": EventType.DONE, "verdict": Verdict.AC})

if __name__ == "__main__":
  main()