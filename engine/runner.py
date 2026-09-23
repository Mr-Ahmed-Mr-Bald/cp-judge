import uuid
import subprocess
from pathlib import Path
from typing import Tuple

class Runner:
  """Runs the binary, pipes the test input to stdin, and captures stdout
  """
  SANDBOX_IMAGE = "cp-judge-sandbox:latest"
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
    
    binary_dir = binary_path.parent.resolve()
    binary_name = binary_path.name
    timeout_sec = time_limit_ms / 1000.0

    # Unique container name to target cleanup on TLE
    container_name = f"judge-exec-{uuid.uuid4().hex[:8]}"

    command = [
      "docker",
      "run",
      "--name",
      container_name,
      "--rm",
      "-i",
      "--read-only",
      "--network",
      "none",
      "--memory",
      f"{memory_limit_mb}m",
      "--memory-swap",
      f"{memory_limit_mb}m",
      "--pids-limit",
      "16",
      "-v",
      f"{binary_dir}:/sandbox:ro",
      "-w",
      "/sandbox",
      Runner.SANDBOX_IMAGE,
      f"./{binary_name}",
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
        stdout, _ = process.communicate(timeout=timeout_sec)
        
        # Return result
        return (str(stdout.strip()), abs(process.returncode), False)
      
    # Timeout
    except subprocess.TimeoutExpired:
      # Forcefully stop and remove the running Docker container
      subprocess.run(
        ["docker", "rm", "-f", container_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
      )
      if (process is not None):
        process.kill()
        process.wait()
      return ("", -1, True)
