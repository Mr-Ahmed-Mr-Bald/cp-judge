# CP Judge

An online judge for competitive programming. Users read a problem, submit C++17
from the browser, and get back one of six verdicts — Accepted, Wrong Answer,
Time Limit Exceeded, Memory Limit Exceeded, Runtime Error, or Compile Error —
after the program has been compiled, run against every test, and checked by a
custom C++ checker.

The project has three parts that talk to each other over the filesystem and a
database, and nothing else:

| Part | Language | What it does |
|---|---|---|
| `engine/` | Python | Compiles, sandboxes, runs and judges one submission. Runs as a command-line tool, independent of the web app. |
| `backend/` | Python (FastAPI) | Accounts, the problem catalogue, submissions, and a worker that calls the engine. |
| `frontend/` | Angular 20 | The web app: statements, submissions, live verdicts, settings. |

---

## Architecture

```
                    browser
                       |
                 :4200 Angular SPA
                       |  relative /api paths
                       v
    +---------------------------------------------+
    |              FastAPI  (:8000)              |
    |  auth · problems · submissions · settings  |
    |  SQLAlchemy -> PostgreSQL                  |
    +---------------------------------------------+
        |            |                 ^
        | enqueues   | claims one job  | streams progress
        v            | (FOR UPDATE     | (JSON lines on stdout)
    +---------+      |  SKIP LOCKED)   |
    | postgres|      v                 |
    +---------+  +---------+           |
        ^       | worker  |-----------+
        |       +---------+           |
        |            |                 |
        |            | spawns          |
        |            v                 |
        |     +--------------------+  |
        |     |  judge engine      |  |
        |     |  (engine/judge.py) |  |
        |     |  g++ -> tests ->   |  |
        |     |  checker -> verdict|  |
        |     +--------------------+  |
        |            |                 |
        |            v                 |
        |     +--------------------+  |
        |     | Docker sandbox     |  |
        |     | no network         |  |
        |     | read-only fs       |  |
        |     | non-root           |  |
        |     | memory + pid caps  |  |
        |     +--------------------+  |
        |                              |
        +--- updates row --------------+
                (verdict, failed_test, current_test)
```

A submission never touches the engine synchronously. The API stores it as
`PENDING` and returns an id; the worker picks it up, runs the engine as a
subprocess, and updates the row as the engine reports progress; the frontend
re-fetches the row until the status is `DONE`.

### Repository layout

```
SPEC.md                    the design document the implementation follows
engine/                    judge engine (no dependency on the web app)
  judge.py                 compile -> run tests -> check -> verdict
  runner.py                Docker sandbox, one container per submission
  compiler.py              g++ wrapper
  checker.py               runs the testlib checker
  add_problem.py           package validation and answer generation
  polygon_to_package.py    Codeforces Polygon export -> judge package
  problems/<slug>/         statement.md, main.cpp, checker.cpp, config.json, tests/
  Dockerfile.sandbox       the sandbox image
  include/testlib.h        header for checkers
regression_suite-1/        5 hand-written solutions: AC, WA, TLE, MLE, overflow
regression_suite-2/        3 more, against a second problem
backend/
  main.py                  API routes
  database.py              SQLAlchemy models
  schemas.py               Pydantic request/response models
  security.py              Argon2 hashing, JWT issue/verify
  worker.py                the judging worker
  init_db.py               creates tables and seeds problems from disk
  migrations/              Alembic revisions
  tests/                   pytest suite for the API
frontend/                  Angular 20 app (see frontend/README.md)
```

---

## Running it

### Prerequisites

Docker, Python 3.12, and Node 22 (the Angular CLI needs 20.19+ or 22.12+).

### 1. Database

```bash
docker run -d --name cp-judge-db \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=cp_judge_db \
  -p 5432:5432 postgres:16
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env      # then edit it, see Configuration
.venv/bin/python init_db.py
.venv/bin/python -m uvicorn main:app --reload --port 8000
```

`init_db.py` creates the tables, seeds the administrator from the environment,
and adds every problem it finds under `engine/problems`. Re-run it after adding
a problem.

Interactive API docs: <http://localhost:8000/docs>

### 3. Worker

```bash
cd backend && .venv/bin/python worker.py
```

The worker needs the Docker CLI and access to the daemon, so run it on the host
rather than in a container.

### 4. Frontend

```bash
cd frontend
npm install
npm start          # http://localhost:4200, proxies /api to :8000
```

### 5. Sandbox image

Built once:

```bash
docker build -t cp-judge-sandbox:latest -f engine/Dockerfile.sandbox engine/
```

---

## Configuration

All backend configuration is read from `backend/.env`:

| Variable | Meaning |
|---|---|
| `DATABASE_URL` | SQLAlchemy connection string |
| `SECRET_KEY` | Signing key for access tokens. Required. |
| `ALGORITHM` | Token algorithm, default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime, default `15` |
| `ADMIN_EMAIL`, `ADMIN_HANDLE`, `ADMIN_PASSWORD` | The administrator, seeded at startup and not modifiable through the API. All three required. |
| `PROBLEMS_DIR` | Where problem packages live |
| `JUDGE_PATH` | Path to `engine/judge.py` |
| `ENGINE_TIMEOUT` | Hard limit on one judging run, in seconds |

`ADMIN_EMAIL` must be a normal address: the login schema validates it, and
libraries reject reserved domains such as `.local`.

---

## How judging works

`engine/judge.py` is a standalone tool, so the engine can be tested without the
web app:

```bash
backend/.venv/bin/python engine/judge.py \
  --problem engine/problems/sample-problem-1 \
  --source /path/to/solution.cpp
```

It prints one JSON object per line:

```
{"event": "compiling"}
{"event": "running", "test": 0}
{"event": "done", "verdict": "WA", "test": 1}
```

Verdicts come out of the run itself:

| Verdict | Cause |
|---|---|
| `AC` | Every test passed the checker |
| `WA` | The checker rejected the output |
| `TL` | The program did not finish a test within the time limit |
| `ML` | The program was killed for exceeding the memory limit |
| `RE` | The program crashed or exited nonzero |
| `CE` | The source did not compile |
| `JE` | The judge itself failed; never the user's fault |

### The sandbox

Submitted code runs in `cp-judge-sandbox:latest` with no network, a read-only
root filesystem, a non-root user, and enforced memory, swap, and process limits.
The submission cannot read the test files, the answer files, or the checker —
only the test input arrives, on standard input.

One container is created per submission and every test is run inside it with
`docker exec`. Creating a container costs roughly half a second on a typical
machine, and doing that per test would charge that startup to the test's own
time limit, so correct solutions failed on short limits. The runner measures
that overhead once per submission and adds it back to each timeout, so the limit
a problem advertises is the limit the program is judged on.

### The job queue

The database is the queue. A worker claims the oldest pending submission inside
a transaction:

```sql
SELECT id FROM submissions WHERE status = 'PENDING'
ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED
```

`SKIP LOCKED` is what makes more than one worker safe: a second worker skips the
row the first one is holding instead of blocking on it, so no submission is ever
judged twice. On startup the worker also resets rows left in `RUNNING` by a
process that died, so a killed worker does not strand a submission.

---

## Adding a problem

A problem is a folder:

```
<slug>/
  statement.md     Markdown, math between $...$ and $$...$$
  main.cpp         the author's solution, used to generate answer files
  checker.cpp      run as ./checker <input> <output> <answer>
  config.json      title, time_limit, memory_limit, tags
  tests/
    00.in          inputs only, numbered from 00 with no gaps, 1 to 100 of them
```

`add_problem.py` validates the package and only stores it if every step passes:
the files and `config.json` are valid, both C++ files compile, the author's
solution runs on every test within the limits to produce the answer files, and
the checker accepts those answers. Then `init_db.py` publishes it to the API.

```bash
cd <repo root>                       # it writes to engine/problems relative to cwd
backend/.venv/bin/python engine/add_problem.py --package_folder <slug>/
cd backend && .venv/bin/python init_db.py
```

### From Codeforces Polygon

If the problem lives on Polygon, export the package and convert it:

```bash
backend/.venv/bin/python engine/polygon_to_package.py <export-dir> --out packages/
backend/.venv/bin/python engine/add_problem.py --package_folder packages/<export-dir>
```

The converter reads the limits, tags, checker, accepted solution, and the
pre-split statement out of the export, converts the LaTeX statement to Markdown
with KaTeX math, inlines the checker's own header so the package stays
self-contained, and replays the generator commands from `problem.xml` to rebuild
the declared test cases from their seeds. Answers are always regenerated by
running the author's solution, never read from the export.

---

## API

| Method and path | Purpose | Access |
|---|---|---|
| `POST /api/register` | Create an account | Public |
| `POST /api/login` | Log in, returns a bearer token | Public |
| `GET /api/me` | The signed-in user | User |
| `PATCH /api/me/handle` | Change handle | User, not admin |
| `PATCH /api/me/password` | Change password | User, not admin |
| `GET /api/problems` | Problem list | Public |
| `GET /api/problems/{slug}` | Problem details and statement | Public |
| `POST /api/problems/{slug}/submissions` | Submit source | User |
| `GET /api/submissions` | Own submissions, optionally filtered by problem | User |
| `GET /api/submissions/{id}` | Status, verdict, and source | Owner only |

Submissions are `PENDING` → `COMPILING` → `RUNNING` (with `current_test`) →
`DONE` (with `verdict` and, when it failed, `failed_test`). Passwords are stored
as Argon2 hashes. Emails and handles are unique through database constraints
rather than a check-then-insert, because two simultaneous registrations would
both pass a check.

---

## Testing

```bash
# API tests
cd backend && .venv/bin/python -m pytest

# Engine regression suites: one solution per expected verdict
cd <repo root>
for c in accepted wa tle mle overflow; do
  backend/.venv/bin/python engine/judge.py \
    --problem engine/problems/sample-problem-1 --source regression_suite-1/$c/main.cpp
done
# same for regression_suite-2 against sample-problem-2

# Frontend build
cd frontend && npm run build
```

The regression suites are the fastest way to tell whether a change to the engine
broke something: together they cover an accepted solution, a wrong answer, a
time limit, a memory limit, an integer overflow caught by the checker, and a
second problem with a different checker.

---

## Notes and limitations

- One submission is judged at a time, by design, so that timings are stable.
- The worker reaches Docker through the host's socket, so it runs on the host
  rather than inside a container.
- C++17 only. No interactive problems, no partial scoring, no contests.
- Access tokens are short-lived; the frontend revalidates on load and returns
  the user to the login page when one expires.
- Problems cannot be edited after they are added. To correct one, add it again
  under a new slug.