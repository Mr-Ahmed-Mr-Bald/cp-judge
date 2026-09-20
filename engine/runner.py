import subprocess
from pathlib import Path
from typing import Tuple

class Runner:
  """Runs the binary, pipes the test input to stdin, and captures stdout
  """
  @staticmethod
  def run(binary_path: Path, input_path: Path, time_limit_ms: int, memory_limit_mb: int) -> Tuple[str, int, bool]:
    """
    Executes binary with test input piped to stdin.

    Returns:
      Tuple[stdout, exit_code, timed_out]
      - stdout: Captured standard output from the program. Empty string in case of timeout.
      - exit_code: 0 for clean exit, > 0 for normal exit code,
        , or abs(signal) if terminated by a POSIX signal.
      - timed_out: True if time limit was exceeded, False otherwise.
    """

    # If binary file does not exist
    if not binary_path.exists():
      return (f"binary file not found", -1, False)
    
    # If input file does not exist
    if not input_path.exists():
      return (f"input file not found", -1, False)
    
    # Command to run
    command = [
      binary_path.resolve()
    ]

    # process is initially None
    process = None
    try:
      # Open input file
      with open(input_path.resolve(), 'r') as infile:

        # Create a process and direct its output to me
        process = subprocess.Popen(
          command,
          stdin=infile,
          stdout=subprocess.PIPE,
          text=True
        )

        # Get the contents of the standard output file
        stdout, _ = process.communicate(timeout=time_limit_ms/1000.0)

        # Return result
        return (str(stdout.strip()), abs(process.returncode), False)
      
    # Timeout
    except subprocess.TimeoutExpired:
      if (process is not None):
        process.kill()
        process.wait()
      return ("", -1, True)
