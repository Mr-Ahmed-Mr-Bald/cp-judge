import subprocess
from pathlib import Path
from typing import Tuple

class Checker:
  """Executes a testlib-compatible C++ checker binary to validate test case output.
  
  Attributes:
  TIMEOUT_SEC (float): Maximum allowed time in seconds for a execution
    process to run before being forcefully terminated.
  """
  TIMEOUT_SEC: float = 10.0

  @staticmethod
  def check(binary_path: Path, input_path: Path, output_path: Path, answer_path: Path) -> Tuple[str, bool]:
    """
    Runs the checker binary against the user's output.

    Args:
      checker_binary: Path to compiled checker executable.
      input_file: Path to problem test input file (.in).
      output_file: Path to candidate's generated output file (.out).
      answer_file: Path to official test answer file (.ans / .sol).

    Returns:
      Tuple[feedback, is_correct]
      - feedback: Feedback from testlib.
      - is_correct: True if exit code == 0, False otherwise.
    """

    # Check if files exist
    for path, name in [
      (binary_path, "Checker binary file"),
      (input_path, "Input file"),
      (output_path, "Output file"),
      (answer_path, "Answer file")
    ]:
      if not path.exists():
        return (f"{name} not found", False)

    # Command to run  
    command = [
      str(binary_path.resolve()),
      str(input_path.resolve()),
      str(output_path.resolve()),
      str(answer_path.resolve())
    ]

    try:
      # Create a process and direct its output to me
      with subprocess.Popen(
        command,
        stderr=subprocess.PIPE,
        text=True
      ) as process:
        
        # Get the contents of the standard error file
        _, stderr = process.communicate(timeout=Checker.TIMEOUT_SEC)
        feedback = stderr.strip()

        # Accepted
        if (process.returncode == 0):
          return (feedback or "Ok", True)
        # WA or PE
        elif (process.returncode == 1 or process.returncode == 2):
          return (feedback or "WA", False)
        # Checker failure
        else:
          return (f"Checker crashed with exit code {process.returncode}: {feedback}", False)
        
    # Timeout    
    except subprocess.TimeoutExpired:
      return ("Checker timed out", False)
