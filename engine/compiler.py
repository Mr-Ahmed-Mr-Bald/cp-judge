import subprocess
from pathlib import Path
from typing import Tuple

from engine.config import COMPILE_TIMEOUT_SEC

class Compiler:
  """Manages the compilation of source code files using system compilers.

  Attributes:
    INCLUDE_DIR (Path): Absolute path to the shared checker headers, anchored to
    this module so it does not depend on the caller's working directory.
  """
  
  INCLUDE_DIR: Path = Path(__file__).resolve().parent / "include"

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
      "g++", "-O2", "-std=c++17",
      f"-I{Compiler.INCLUDE_DIR}",
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
        _, stderr = process.communicate(timeout=COMPILE_TIMEOUT_SEC)
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