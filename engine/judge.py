import sys
import json
import argparse
import tempfile
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.protocol import EventType, Verdict, emit_event
from engine.compiler import Compiler
from engine.runner import Sandbox
from engine.checker import Checker
from engine.package_spec import (
  TESTS_DIR, CHECKER_CPP, CONFIG_JSON, INPUT_SUFFIX, ANS_SUFFIX, OUTPUT_FILE
)

def validate_problem_package(problem_path: Path) -> Tuple[bool, str]:
  """Ensures the problem directory is valid before starting execution."""
  
  for path, name in [
    (problem_path, "Problem folder"),
    (problem_path / TESTS_DIR, "Tests folder"),
    (problem_path / CHECKER_CPP, CHECKER_CPP),
    (problem_path / CONFIG_JSON, CONFIG_JSON),
  ]:
    if not path.exists():
      return (False, f"{name} not found")
  
  return True, ""

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

  # Validate problem package
  ok, error_message = validate_problem_package(problem_path)
  if (not ok):
    emit_event(EventType.DONE, verdict=Verdict.JE, message=error_message)
    sys.exit(1)

  # Ensure source file exists
  if (not source_path.exists() or not source_path.is_file()):
    emit_event(
      EventType.DONE, 
      verdict=Verdict.JE, 
      message= f"Source file not found: {source_path}"
    )
    sys.exit(1)

  # Get configuration
  config_path = problem_path / CONFIG_JSON
  with open(config_path, "r", encoding="utf-8") as f:
    problem_config = json.load(f)

  # Start compiling

  # Create a temporary folder as a judging environment
  with tempfile.TemporaryDirectory() as tmp_dir:
    work_dir = Path(tmp_dir)
    user_binary = work_dir / "user_binary"
    checker_binary = work_dir / "checker_binary"
    emit_event(EventType.COMPILING)

    # Compiling source code
    error_message, success = Compiler.compile(source_path, user_binary)
    if (not success):
      emit_event(EventType.DONE, verdict=Verdict.CE, message= error_message)
      sys.exit(0)

    # Compiling checker
    checker_source = problem_path / CHECKER_CPP
    error_message, success = Compiler.compile(checker_source, checker_binary)
    if (not success):
      emit_event(EventType.DONE, verdict=Verdict.JE, message= error_message)
      sys.exit(1)

    # Validate test files
    tests_dir = problem_path / TESTS_DIR
    test_files = sorted(list(tests_dir.glob(f"*.{INPUT_SUFFIX}")))
    for test_idx, test_file in enumerate(test_files):
      if (not test_file.with_suffix(f".{ANS_SUFFIX}").exists()):
        emit_event(
          EventType.DONE,
          verdict=Verdict.JE, # Judge's fault
          test=test_idx,
          message= "Answer file does not exist"
        )
        sys.exit(1)

    # One sandbox for the whole submission: the container is created once and
    # each test runs inside it, so container startup is not charged to the
    # problem's time limit.
    try:
      sandbox = Sandbox(problem_config["memory_limit"], user_binary.parent)
      sandbox.start()
    except (RuntimeError, OSError) as error:
      emit_event(EventType.DONE, verdict=Verdict.JE, message= str(error))
      sys.exit(1)

    with sandbox:
      for test_idx, test_file in enumerate(test_files):
        emit_event(EventType.RUNNING, test=test_idx)

        pstdout, exit_code, timed_out = sandbox.run(
          user_binary.name, test_file, problem_config["time_limit"]
        )

        # Timeout
        if (timed_out):
          emit_event(EventType.DONE, verdict=Verdict.TL,test=test_idx)
          sys.exit(0)

        # Memory limit
        if (exit_code == 137):
          emit_event(EventType.DONE, verdict=Verdict.ML, test=test_idx)
          sys.exit(0)

        # Runtime error
        if (exit_code != 0):
          emit_event(EventType.DONE, verdict=Verdict.RE, test=test_idx)
          sys.exit(0)

        # Save program stdout to temporary file for checker
        out_file = work_dir / OUTPUT_FILE
        out_file.write_text(pstdout, encoding="utf-8")

        feedback, is_correct = Checker.check(checker_binary, test_file, out_file, test_file.with_suffix(f".{ANS_SUFFIX}"))
        if (not is_correct):
          emit_event(EventType.DONE, verdict=Verdict.WA, test=test_idx, message=feedback)
          sys.exit(0)

    emit_event(EventType.DONE, verdict=Verdict.AC)

if __name__ == "__main__":
  main()