import re
import sys
import json
import shutil
import argparse

from pathlib import Path
from compiler import Compiler
from runner import Sandbox
from checker import Checker

def fail(msg: str):
  """Prints error message, and terminates with exit code 1"""
  print(f"Error: {msg}", file=sys.stderr)
  sys.exit(1)

def validate_slug(slug: str):
  """Validates problem slug"""
  if (not re.match(r"^[A-Za-z0-9_-]+$", slug)):
    fail(f"Invalid package slug '{slug}': Slugs must contain only letters, numbers, hyphens, and underscores.")

def validate_config(file_path: Path) -> dict:
  """Validates config.json file for a problem
  
  Returns extracted data as a dictionary
  """
  data = {}
  try:
    with open(file_path, "r", encoding="utf-8") as f:
      data: dict = json.load(f)
  except Exception as e:
    fail(f"Failed to parse {file_path.name}: {e}")

  allowed_keys: set = {"title", "time_limit", "memory_limit", "tags"}
  if (set(data.keys()) != allowed_keys):
    fail("config.json must contain exactly 'title', 'time_limit', 'memory_limit', and 'tags'.")
  
  if not isinstance(data["title"], str) or not data["title"].strip():
    fail("config.json: 'title' must be a non-empty string.")

  if not isinstance(data["time_limit"], int) or not (100 <= data["time_limit"] <= 10000):
    fail("config.json: 'time_limit' must be an integer between 100 and 10000.")

  if not isinstance(data["memory_limit"], int) or not (32 <= data["memory_limit"] <= 1024):
    fail("config.json: 'memory_limit' must be an integer between 32 and 1024.")

  if not isinstance(data["tags"], list) or not all(isinstance(t, str) for t in data["tags"]):
    fail("config.json: 'tags' must be a list of strings.")

  return data

def validate_tests(tests: Path) -> list[Path]:
  """Validates 'tests' folder for a problem
  
  Returns a list of file paths to the individual test files
  """
  if not tests.is_dir():
    fail(f"'tests' directory not found.")
  
  test_files = sorted(tests.glob("*.in"))
  if not (0 <= len(test_files) <= 100):
    fail(f"Number of tests must be between 0 and 100. Found {len(test_files)}")

  for idx, path in enumerate(test_files):
    if (path.name != f"{idx:02d}.in"):
      fail("Invalid test file naming sequence.")

  return test_files
  

def main():
  parser = argparse.ArgumentParser(description="Validate and Register a Problem Package")
  parser.add_argument("--package_folder", type=Path, help="Path to package folder")
  
  args = parser.parse_args()
  pkg: Path = args.package_folder.resolve()

  if not pkg.is_dir():
    fail(f"Directory '{pkg}' does not exist.")
  
  slug = pkg.name
  validate_slug(slug)

  problem = Path("engine/problems") / slug
  if problem.exists():
    fail(f"Problem with the same slug already exists.")

  statement_file = pkg / "statement.md"
  config_file = pkg / "config.json"
  main_file = pkg / "main.cpp"
  checker_file = pkg / "checker.cpp"
  tests = pkg / "tests"

  # Make sure files exist
  for file in [statement_file, config_file, main_file, checker_file]:
    if not file.exists():
      fail(f"Required file '{file.name}' is missing from package.")

  # Validate config.json and tests folder
  problem_config: dict = validate_config(config_file)
  problem_tests: list[Path] = validate_tests(tests)

  print("Package contains required files")

  main_binary = pkg / "main_binary"
  checker_binary = pkg / "checker_binary"

  # Compile main solution file
  error_message, success = Compiler.compile(main_file, main_binary)
  if not success:
    fail(f"Compilation of main solution '{main_file}' failed: {error_message}")

  # Compile checker file
  error_message, success = Compiler.compile(checker_file, checker_binary)
  if not success:
    fail(f"Compilation of checker '{checker_file}' failed: {error_message}")

  print("Main solution and checker compiled successfully")

  # Generate answers according to main solution. One sandbox for every test,
  # so a problem with a tight time limit is not failed by container startup.
  answer_files: list[Path] = []
  try:
    sandbox = Sandbox(problem_config["memory_limit"], main_binary.parent)
    sandbox.start()
  except (RuntimeError, OSError) as error:
    fail(f"Could not start sandbox: {error}")

  with sandbox:
    for test_file in problem_tests:
      answer_file = test_file.with_suffix(".ans")
      stdout, exit_code, timed_out = sandbox.run(
        main_binary.name,
        test_file,
        problem_config["time_limit"]
      )

      if timed_out:
        fail(f"Main solution timed out on test '{test_file.name}'.")
      
      if (exit_code != 0):
        fail(f"Main solution produced wrong answer on test '{test_file.name}'")

      answer_file.write_text(stdout, encoding="utf-8")
      answer_files.append(answer_file)

  print("All tests executed")

  # Ensure checker acknowleges author answers
  for test_file, answer_file in zip(problem_tests, answer_files):
    feedback, is_correct = Checker.check(checker_binary, test_file, answer_file, answer_file)
    if not is_correct:
      fail(f"Checker rejected valid answer on test '{test_file.name}': {feedback}")

  print("All tests passed checker")

  # Remove termporary files
  main_binary.unlink(missing_ok=True)
  checker_binary.unlink(missing_ok=True)

  # Copy problem folder
  problem.parent.mkdir(exist_ok=True)
  shutil.copytree(pkg, problem)
  print(f"Problem '{slug}' added")

if __name__ == "__main__":
  main()