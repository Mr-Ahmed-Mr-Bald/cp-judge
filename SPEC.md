# Competitive Programming Judge Webapp: Specification (v0.1)

## 1. Purpose and scope

A web application where users read programming problems, submit C++ solutions, and receive an automatic verdict. Administrators add problems from the command line. The system is deliberately small: no contests, ratings, or user profile pages.

Values marked **(default)** are proposed values that the design phase may adjust. Everything else was decided explicitly.

## 2. Non-goals

- Contests, scoreboards, ratings, editorials, comments, or discussion.
- Partial scoring or subtasks. Scoring is all-or-nothing.
- Languages other than C++.
- Interactive problems, validators, and generators.
- Profile pages and solving statistics.
- Email verification and password reset.
- Editing or removing a problem after it is added. To correct a problem, add it again under a new slug.
- Distributed judging. One worker judges one submission at a time.

## 3. Definitions

- **Problem package**: the folder an administrator supplies for one problem (Section 5).
- **Slug**: the package folder name, used as the problem's unique identifier in URLs.
- **Answer file**: the expected output for one test, produced by running the author solution on that test's input.
- **Checker**: a C++ program supplied with the problem that decides whether a submission's output is correct.
- **Judge engine**: a standalone program that compiles and runs one submission against one problem and reports a verdict (Section 7).
- **Worker**: a backend process that takes pending submissions from the database, calls the judge engine, and stores results.
- **Sandbox**: a restricted environment in which submitted code runs (Section 8).
- **Verdict**: the final outcome of judging a submission (Section 6).

## 4. Users and functional requirements

### 4.1 Visitor

- Register with an email, a handle, and a password.
- Log in with email and password.

### 4.2 Registered user

- List problems (title, tags, limits) and open a problem page showing the rendered statement, limits, and tags.
- Submit C++ source code for a problem.
- See the status and verdict of a submission, updating without a page reload.
- List their own submissions, and view the source of their own submissions only.
- Change their handle (if the new handle is available) and their password.

Rules **(default)**: handles are 3 to 20 characters from `A-Z a-z 0-9 _`, unique case-insensitively. Emails are unique. Passwords have at least 8 characters and are stored only as salted hashes. Source code is at most 64 KiB.

### 4.3 Administrator

- The administrator is a user created by the system at startup from configuration (environment variables). It cannot be deleted or modified, including its handle and password.
- Problems are added with a command-line script run on the server: `add-problem <package_folder>`. It validates the package (Section 5.5) and stores the problem only if validation succeeds. Adding an existing slug is rejected.

## 5. Problem package

### 5.1 Layout

```
<slug>/
  statement.md
  main.cpp
  checker.cpp
  config.json
  tests/
    00.txt
    01.txt
    ...
```

### 5.2 Files

- `statement.md`: Markdown with LaTeX math between `$...$` (inline) and `$$...$$` (display), rendered in the browser with KaTeX.
- `main.cpp`: the author solution. It reads standard input and writes standard output.
- `checker.cpp`: the checker (Section 5.4).
- `config.json`: `{ "title": string, "time_limit_ms": integer, "memory_limit_mb": integer, "tags": [string] }`. All fields are required; `tags` may be empty.
- `tests/`: input files only, named with two digits starting at `00` with no gaps. Between 1 and 100 tests.

### 5.3 Limits

The time limit applies per test. The memory limit applies to the process running the submission. Bounds **(default)**: time limit 100 to 10000 ms, memory limit 16 to 1024 MB.

### 5.4 Checker contract

The checker is invoked as `./checker <input> <output> <answer>`, where `input` is the test input, `output` is the submission's output, and `answer` is the answer file. It communicates through its exit code:

| Exit code | Meaning |
|---|---|
| 0 | Output accepted |
| 1 | Output rejected (wrong answer) |
| other, crash, or timeout | Judge error |

The argument order follows testlib, so testlib-based checkers can be adopted later. Checkers are trusted (written by the administrator) and have a wall-clock timeout of 10 s **(default)**.

### 5.5 Package validation

`add-problem` performs these steps and aborts at the first failure:

1. Required files exist, `config.json` parses with valid values, and the test count is in range and contiguous.
2. `main.cpp` and `checker.cpp` compile.
3. `main.cpp` runs on every test within the stated limits and exits with code 0. Its outputs are stored as the answer files.
4. The checker accepts the answer file as the output for every test (invoked with `answer` in both the `output` and `answer` positions).

## 6. Judging semantics

### 6.1 Verdicts

| Verdict | Meaning |
|---|---|
| ACC | All tests passed |
| WA | The checker rejected the output on some test |
| TLE | The time limit was exceeded on some test |
| MLE | The memory limit was exceeded on some test |
| RE | The program crashed or exited with a nonzero code |
| CE | The source failed to compile |

JE (Internal Judge Error) is the seventh verdict, used when the judge itself fails — checker error, sandbox failure, or a missing problem file. It is never the user's fault.

### 6.2 Procedure

1. Compile the source with `g++ -O2 -std=c++17` under a compile timeout of 5 s **(default)**. On failure, the verdict is CE.
2. For each test `i` in increasing order, run the program with the test input on standard input, under the problem's limits.
   - Time limit exceeded gives TLE. Memory limit exceeded (out-of-memory kill) gives MLE. Any other abnormal termination or nonzero exit code gives RE.
   - Otherwise run the checker. Exit code 0 continues to the next test, 1 gives WA, anything else gives JE.
3. Judging stops at the first non-accepted test. If every test is accepted, the verdict is ACC.

The result stores the verdict and, for TLE, MLE, RE, and WA, the index of the failing test. No further diagnostics (signals, access violations, compiler messages) are stored or shown.

## 7. Judge engine and submission lifecycle

### 7.1 Submission states

`status` moves through `PENDING` (queued), `COMPILING`, `RUNNING` (with `current_test`), and `DONE` (with the verdict). Only `DONE` submissions have a verdict.

### 7.2 Flow

1. A user submits. The backend stores the submission as `PENDING` and returns its id immediately.
2. The worker repeatedly selects the oldest `PENDING` submission, runs the judge engine on it, and updates the row as the engine reports progress. One submission is judged at a time so that timings are stable.
3. The frontend re-fetches the submission every 1 to 2 seconds until its status is `DONE`.

### 7.3 Engine interface

The engine is a command-line program, testable without the backend:

```
judge --problem <stored_problem_dir> --source <source.cpp>
```

It writes one JSON object per line to standard output:

```
{"event": "compiling"}
{"event": "running", "test": 23}
{"event": "done", "verdict": "WA", "test": 27}
```

`verdict` is one of the seven verdicts: AC, WA, TL, ML, RE, CE, or JE. `test` is present only for failing tests. The stored problem directory contains the package files plus the answer files created during validation.

## 8. Sandbox requirements

Submitted code is run with these properties, using Docker (one container per submission, reused across all tests via `docker exec`):

- No network access.
- Read-only root filesystem, with no access to tests, answer files, or the checker other than the test input supplied on standard input.
- Memory limit, process count limit, and CPU restriction enforced by the container.
- Non-root user.
- A wall-clock timeout matching the time limit.

Users are assumed non-malicious, so hardening beyond this is out of scope.

## 9. Data model

**users**: `id`, `email` (unique), `handle` (unique, case-insensitive), `password_hash`, `role` (`user` or `admin`), `created_at`.

**problems**: `id`, `slug` (unique), `title`, `statement_md`, `time_limit_ms`, `memory_limit_mb`, `tags`, `test_count`, `created_at`. Tests, answers, and the checker live on disk under the stored problem directory, not in the database.

**submissions**: `id`, `user_id`, `problem_id`, `source_code`, `status`, `verdict` (nullable), `failed_test` (nullable), `current_test` (nullable), `created_at`, `judged_at` (nullable).

## 10. Web API (outline)

| Method and path | Purpose | Access |
|---|---|---|
| `POST /api/register`, `POST /api/login` | Account creation and login | Public |
| `PATCH /api/me/handle`, `PATCH /api/me/password` | Change handle or password | User (not admin) |
| `GET /api/problems` | List problems | Public |
| `GET /api/problems/{slug}` | Problem details and statement | Public |
| `POST /api/problems/{slug}/submissions` | Submit source code | User |
| `GET /api/submissions/{id}` | Status, verdict, and source | Owner only |
| `GET /api/submissions` | Own submissions, optionally filtered by problem | User |

## 11. Deferred to the design phase

- Technology stack for the backend, database, frontend, and judge engine.
- Authentication mechanism (sessions or tokens).
- Sandbox implementation details and how the worker reaches Docker.
- Caching of compiled checkers.
- Deployment (Docker Compose locally, one Linux server for a live demo).
- Optional extensions: showing compiler output for CE, pagination, per-user solved markers.
