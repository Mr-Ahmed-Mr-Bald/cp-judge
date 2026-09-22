import subprocess
from pathlib import Path
from typing import Tuple

class Compiler:
  """Manages the compilation of source code files using system compilers.

  Attributes:
    TIMEOUT_SEC (float): Maximum allowed time in seconds for a compilation
    process to run before being forcefully terminated.
  """
  TIMEOUT_SEC: float = 10.0

  @staticmethod
  def compile(source_path: Path, binary_path: Path) -> Tuple[str, bool]:
    """
    Compiles a C++ source file using g++ -O2 -std=c++17

    Returns (error_message, success)
    """
    # If source file does not exist
    if not source_path.exists():
      return (f"source file not found: {source_path}", False)
    
    # Command to run
    command = [
      "g++",
      "-O2",
      "-std=c++17",
      str(source_path.resolve()),
      "-o",
      str(binary_path.resolve())
    ]
    
    try:
      # Create a process and direct its output to me
      with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
      ) as process:
        
        # Get the contents of the standard error file
        _, stderr = process.communicate(timeout=Compiler.TIMEOUT_SEC)
        # Success
        if process.returncode == 0:
          return ("", True)
        
        # Failure
        return (str(stderr.strip()), False)

    # Timeout  
    except subprocess.TimeoutExpired:
      return ("compilation timed out", False)
    
    # g++ not found
    except FileNotFoundError:
      return ("g++ compiler not found", False)