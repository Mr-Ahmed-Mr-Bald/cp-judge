# CP Judge — frontend

Angular 20 single-page app for the judge. It talks only to the HTTP API in
`SPEC.md` section 10; there is no server-side rendering and no coupling to the
engine.

## Running it

The Angular CLI needs Node 20.19+ or 22.12+. The Node that is on the Windows
side of this WSL machine is 18, so a Linux Node 22 was installed in
`~/.local/node`:

```bash
export PATH="$HOME/.local/node/bin:$PATH"   # node v22.14.0
cd frontend
npm install
npm start                                     # http://localhost:4200
```

`npm start` runs `ng serve` with `proxy.conf.json`, which forwards `/api` to
`http://localhost:8000`. Because the frontend always calls relative `/api`
paths, the same production bundle works unchanged behind a reverse proxy that
serves `dist/frontend/browser` and proxies `/api` to the backend.

The backend, the database and the worker must be running for anything but the
problem list and problem pages to have data:

```bash
cd backend
.venv/bin/python -m uvicorn main:app --port 8000   # API + docs at /docs
.venv/bin/python worker.py                          # judge worker
```

## Layout

```
src/app/
  app.ts, app.routes.ts, app.config.ts   shell, routes, providers
  core/                                  everything that is not a page
    models.ts        TypeScript mirrors of backend/schemas.py
    api.service.ts   typed wrapper over the endpoints
    auth.service.ts  token + user, stored in localStorage
    auth.interceptor.ts  attaches the token, handles an expired session
    api-error.ts     409 / 401 / 422 -> one message plus per-field messages
    markdown.service.ts  Markdown + KaTeX for statements
    verdict.ts       verdict codes -> labels, hints, colours
    time.ts          relative time, judging duration, limit formatting
    theme.service.ts dark / light palettes
  ui/                                   shared presentational components
    header.ts, statement.ts, verdict-badge.ts
  features/
    auth/login.ts, auth/register.ts
    problems/problem-list.ts, problems/problem-detail.ts
    submissions/submission-detail.ts, submissions/my-submissions.ts
    settings/settings.ts
    not-found.ts
```

Routes are lazy-loaded, so KaTeX only downloads when a problem page is opened.

## What each page uses

| Page | Endpoints |
|---|---|
| Problem list | `GET /api/problems` |
| Problem page | `GET /api/problems/{slug}`, `POST /api/problems/{slug}/submissions`, `GET /api/submissions?problem_slug=…&limit=5` |
| Submission page | `GET /api/submissions/{id}` every 1.5 s until `DONE`, `GET /api/problems/{slug}` for the test count |
| My submissions | `GET /api/submissions?problem_slug=…&limit=50`, `GET /api/problems` for the filter |
| Settings | `PATCH /api/me/handle`, `PATCH /api/me/password` |
| Header / session | `POST /api/login`, `POST /api/register` (then logs in), `GET /api/me` |

## Behaviour worth knowing

- **Session.** `POST /api/login` returns a token that expires after 15 minutes
  (`ACCESS_TOKEN_EXPIRE_MINUTES`). The token and the user object live in
  `localStorage`; on bootstrap `GET /api/me` revalidates them, and the
  interceptor sends the visitor to `/login?reason=expired` on any later 401.
  `PATCH /api/me/password` also answers 401 for a wrong *current* password, so
  that path is excluded from the session-expiry redirect.
- **Registration.** The API returns the user but no token, so the frontend logs
  the new account in before navigating. That is one chained observable, not a
  fire-and-forget request, so a fast reload cannot lose the session.
- **Field errors.** `422` bodies are Pydantic validation arrays keyed by
  `loc`; `409` bodies are free text ("Handle already taken") and are mapped
  back to a field by wording. A failed *login* never says which field was
  wrong, matching the API's generic message.
- **Verdicts.** The engine emits `AC WA TL ML RE CE JE`. `TL` and `ML` are the
  engine's names for the spec's TLE and MLE; the UI shows the long names.
- **Polling.** The submission page polls every 1.5 s and stops at `DONE` (or
  when the component is destroyed). My-submissions polls every 2 s only while
  at least one row is still not `DONE`.
- **Drafts.** The source you are typing is saved per problem in `localStorage`,
  so a reload does not lose it.
- **Statements.** `statement.md` is rendered with `marked` plus a KaTeX
  extension for `$…$` and `$$…$$`. Fenced blocks and inline code are lifted out
  before parsing so a `$` inside a sample input is never treated as maths, and
  raw HTML in a statement is escaped.

## Backend changes this frontend relies on

`GET /api/submissions` and `GET /api/submissions/{id}` return `problem_slug`
and `problem_title` (and `failed_test` / `judged_at` on the list) so a row can
be rendered and linked without a second lookup. This was added to the API while
building this page; the response models only grew fields, so older clients keep
working.

## Known API quirks

- `ADMIN_EMAIL=admin@judge.local` cannot be used to log in: the login schema
  validates emails with `EmailStr`, and `email_validator` rejects `.local` as a
  reserved domain. Change `ADMIN_EMAIL` in `backend/.env` to a normal domain
  (and the seeded row in the database) to try the administrator flow.