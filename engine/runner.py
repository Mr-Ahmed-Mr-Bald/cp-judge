import subprocess
import time
import uuid
from pathlib import Path
from typing import Tuple

class Sandbox:
  """Runs a candidate binary inside the sandbox, one container per submission.

  Creating a container costs 0.4-0.7s on this host, and `docker run` returns
  only once the container is up. Running one container per test therefore put
  that startup cost inside the measured window and against the problem's time
  limit: a 1s limit left roughly 0.35s of real budget, and correct solutions
  were given TLE.

  Starting the container once and entering it with `docker exec` costs about
  0.15s per test instead, so most of the startup cost leaves the measured
  window. The remainder is measured per submission (see CALIBRATION_RUNS) and
  added back to the timeout, so the limit a problem advertises is the limit
  the program is actually judged on.

  The sandbox itself is unchanged: --memory, --memory-swap, --pids-limit,
  --network none and --read-only are container-level limits, so they apply to
  every process run inside it exactly as they did to the single process of a
  per-test container. The image already runs as the unprivileged judgeuser.
  """

  SANDBOX_IMAGE: str = "cp-judge-sandbox:latest"
  # Keeps the container alive between tests so `docker exec` has somewhere to run.
  IDLE_COMMAND: list[str] = ["sleep", "infinity"]
  # Empty execs timed to measure this submission's harness overhead.
  CALIBRATION_RUNS: int = 3
  # Never hand back more than this, however slow the host is.
  MAX_COMPENSATION_SEC: float = 0.5
  PIDS_LIMIT: str = "16"

  def __init__(self, memory_limit_mb: int, binary_dir: Path):
    """
    Args:
      memory_limit_mb: The memory cap for the whole container, in MB.
      binary_dir: Host directory holding the binary; mounted read-only at /sandbox.
    """
    self.memory_limit_mb = memory_limit_mb
    self.binary_dir = Path(binary_dir).resolve()
    self.name = f"judge-exec-{uuid.uuid4().hex[:8]}"
    self.compensation_sec = 0.0
    self._running = False

  def start(self) -> None:
    """Creates the sandbox container and measures its per-exec overhead."""
    if self._running:
      return

    command = [
      "docker", "run", "-d",
      "--name", self.name,
      "--read-only",
      "--network", "none",
      "--memory", f"{self.memory_limit_mb}m",
      "--memory-swap", f"{self.memory_limit_mb}m",
      "--pids-limit", self.PIDS_LIMIT,
      "-v", f"{self.binary_dir}:/sandbox:ro",
      "-w", "/sandbox",
      self.SANDBOX_IMAGE,
      *self.IDLE_COMMAND,
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
      raise RuntimeError(
        f"could not start sandbox: {(result.stderr or result.stdout).strip()}"
      )

    self._running = True
    self.compensation_sec = self._measure_overhead()

  def _measure_overhead(self) -> float:
    """Times empty execs so their cost is not charged to the first test."""
    samples = []
    for _ in range(self.CALIBRATION_RUNS):
      started = time.monotonic()
      subprocess.run(
        ["docker", "exec", self.name, "/bin/true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
      )
      samples.append(time.monotonic() - started)

    if not samples:
      return 0.0

    samples.sort()
    median = samples[len(samples) // 2]
    return min(median, self.MAX_COMPENSATION_SEC)

  def stop(self) -> None:
    """Removes the container. Safe to call more than once."""
    if not self._running:
      return

    subprocess.run(
      ["docker", "rm", "-f", self.name],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
    )
    self._running = False

  def __enter__(self) -> "Sandbox":
    self.start()
    return self

  def __exit__(self, *_: object) -> None:
    self.stop()

  def run(
    self,
    binary_name: str,
    input_path: Path,
    time_limit_ms: int,
    _retry: bool = True
  ) -> Tuple[str, int, bool]:
    """
    Runs the binary inside the sandbox with the test input on stdin.

    Returns:
      (stdout, exit_code, timed_out)
      - stdout: Captured standard output. Empty string on timeout.
      - exit_code: 0 for a clean exit, >0 for a normal exit code, or the
        absolute value of the signal that killed the process (so a segfault
        shows up as 11).
      - timed_out: True if the time limit was exceeded.
    """
    if not self._running:
      # A previous test hit its limit and took the container down with it.
      self.start()

    command = [
      "docker", "exec", "-i",
      "--workdir", "/sandbox",
      self.name,
      f"./{binary_name}",
    ]

    timeout_sec = time_limit_ms / 1000.0 + self.compensation_sec
    process = None

    try:
      with open(Path(input_path).resolve(), 'r') as infile:
        process = subprocess.Popen(
          command,
          stdin=infile,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
          text=True
        )

        stdout, stderr = process.communicate(timeout=timeout_sec)

        # 125 is docker's own failure code, not the program's: the
        # container went away underneath us. Start a new one and try once.
        if (process.returncode == 125 and _retry):
          self.stop()
          self.start()
          return self.run(binary_name, input_path, time_limit_ms, _retry=False)

        return (str(stdout.strip()), abs(process.returncode), False)

    except subprocess.TimeoutExpired:
      # Killing the docker client leaves the program running inside the
      # container, so the container itself is removed: that is the only way to
      # guarantee nothing survives. The next run() starts a fresh one.
      if (process is not None):
        process.kill()
        process.wait()
      self.stop()
      return ("", -1, True)

    except FileNotFoundError:
      self.stop()
      return (f"docker executable not found", -1, False)

class Runner:
  """One-shot API for running a single binary against a single test.

  Kept for callers that do not want to manage a container's lifetime. Anything
  running more than one test should use Sandbox directly so the container is
  created once instead of once per test.
  """

  @staticmethod
  def run(
    binary_path: Path,
    input_path: Path,
    time_limit_ms: int,
    memory_limit_mb: int
  ) -> Tuple[str, int, bool]:
    if not binary_path.exists():
      return (f"binary file not found", -1, False)

    if not input_path.exists():
      return (f"input file not found", -1, False)

    with Sandbox(memory_limit_mb, binary_path.parent) as sandbox:
      return sandbox.run(binary_path.name, input_path, time_limit_ms)