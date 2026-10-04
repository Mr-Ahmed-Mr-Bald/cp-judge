# Limits on Compilation and Checking times
COMPILE_TIMEOUT_SEC: float = 10.0
CHECKER_TIMEOUT_SEC: float = 10.0

SANDBOX_IMAGE: str = "cp-judge-sandbox:latest"
# Keeps the container alive between tests so `docker exec` has somewhere to run.
IDLE_COMMAND: list[str] = ["sleep", "infinity"]
# Empty execs timed to measure this submission's harness overhead.
CALIBRATION_RUNS: int = 3
# Never hand back more than this.
MAX_COMPENSATION_SEC: float = 0.5
# Limit on number of spawned processes
PIDS_LIMIT: str = "16"