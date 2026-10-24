# WebTrace

A working single-workspace QA dashboard built on the existing React/Vite frontend and FastAPI/Playwright backend. Core testing needs no AI API key.

## Start on Windows

Run these commands from this project directory:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
npm --prefix frontend ci
npm run build
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/**. FastAPI serves the compiled website and API together. Keep one backend process running; avoid `--reload` during tests because restarts interrupt execution.

For frontend development, keep the backend running and use a second terminal:

```powershell
npm run dev
```

Open the Vite URL printed in that terminal (normally http://127.0.0.1:5173). Its proxy connects `/api`, `/health`, `/demo`, and `/screenshots` to port 8000.

## Use the website

1. Open Dashboard, then New Test.
2. Select **Use defective sandbox** and **Complete assessment flow**.
3. Confirm permission and click **Start Test**.
4. Actual Chromium execution signs in using synthetic data, starts the assessment, selects an answer, and checks submission.
5. Open the report's issue rows to inspect severity, independent priority, reproduction steps, and actual screenshot evidence.
6. Change issue status/priority or rerun the test. History and recurrence data persist in SQLite.
7. Select **Use normal sandbox** to compare a clean flow.

## Implemented

- Responsive dashboard, New Test, searchable History, Reports and Settings pages.
- Midnight and light themes saved in browser storage; reduced-motion handling.
- Recharts metrics and issue charts use backend records. No seeded/fabricated dashboard results.
- Deterministic planner, page explorer, real Playwright execution, existing visual auditor, reporting and orchestration.
- UI/accessibility checks, synthetic login, navigation destinations, required-field validation, assessment/submission and 1280/768/390px overflow checks.
- Live logs and execution-stage statuses, real original/annotated screenshots, JSON reports, expected CSS selectors and saved test configurations.
- Optional bounded same-origin discovery (up to five pages), DOM field inventories, page screenshots and HTTP statuses.
- Console/JavaScript/network diagnostics, optional native Playwright trace ZIP downloads, step timings, and expected/actual failure details with rule-based guidance.
- SQLAlchemy/SQLite run snapshots and tables for steps, observations, screenshots, issue occurrences, status history and saved tests.
- Recurrence compares issue fingerprints across distinct run IDs. Status changes are per occurrence.
- Public-URL validation, private/reserved destination rejection, per-request/redirect checks, blocked non-GET requests and WebSockets, disabled downloads/service workers, two concurrent runs and a 120-second execution timeout.
- Evidence routes only serve registered PNG filenames within the evidence directory.

## Verified results

See `verification/core-results.json` for actual run IDs and counts. The successful integration suite ran 12 browser tests plus a rerun:

| Objective | Normal | Defective |
| --- | --- | --- |
| Assessment | 9/9 steps; 0 issues | 8/9 steps; submission failure + 2 UI issues |
| Required fields | 2/2; 0 issues | 1/2; empty fields accepted + 2 UI issues |
| Responsive | 4/4; 0 issues | 3/4; mobile overflow + 2 UI issues |
| Navigation | 4/4; 0 issues | 3/4; placeholder destination + 2 UI issues |
| Login | 5/5; 0 issues | 5/5; 2 independent UI issues |
| Custom selector audit | 1/1; 0 issues | 1/1; 2 UI issues |

The suite also verified actual PNG signatures, rerun history, recurrence, status/priority changes, status history, five unsafe URL rejections and unregistered-evidence rejection. Browser inspection verified the dashboard, new-test submission, issue details, rerun control, and theme persistence. Backend restart verified that previous runs and an issue-status update survived.

Run the integration suite against a running backend:

```powershell
python scripts/verify_core.py
```

These tests create real run records, screenshots and reports. Earlier development/verification runs are retained honestly in history, including the normal-demo hidden-image problem fixed during verification.

## Scope and limitations

- This is a single-workspace local application, with no multi-user login or per-user isolation. Public hosting has not been deployed.
- External websites receive read-only UI checks. Interactive login/form/submission flows are implemented for the bundled fictional assessment only; external workflows receive a clear scope notice.
- Custom instructions are saved as context; custom mode audits the UI and expected CSS selectors. Arbitrary natural-language browser actions, payments, CAPTCHAs and destructive actions are unsupported.
- Existing optional AI provider code is preserved but not enabled. The current execution path is deterministic and never simulates a browser run.
- Explorer defaults to one page; the UI can inspect up to five pages at one link level. The API supports up to two levels. Discovery skips query links, cross-origin navigation and action-like paths; it does not claim complete site coverage. Navigation checks remain scoped to destinations and the demo help link.
- Visual audit findings are heuristics requiring review, not a full WCAG certification. Baselines are per URL, and pixel differences may include legitimate changes.
- Application URL filtering is not a replacement for network isolation against hostile websites or DNS rebinding. Public production use needs authentication and isolated browser egress.
- Docker configuration is supplied but unverified locally because the Docker engine is not running.

## Data and optional container deployment

By default, SQLite is `backend/webtrace.db`; screenshots, baselines and reports stay under `backend/`. Set `WEBTRACE_DATA_DIR` to relocate runtime data. Back up that entire directory. Keep a single backend process/replica for this SQLite architecture.

`Dockerfile` builds the frontend and installs Chromium for a Python container. `compose.yaml` keeps a named data volume and binds the service to local port 8000:

```powershell
docker compose up --build
```

If deploying later to Render or Railway, use the Dockerfile, port 8000, `/health` health check, `WEBTRACE_DATA_DIR=/data`, and a persistent volume mounted at `/data`. Public access, credentials, and any paid hosting resources must be configured in the connected hosting account. Neither account was connected or deployed during this work.

## Suggested GitHub repository

The user-suggested [Multi-Agent-QA-Orchestrator](https://github.com/sakshammhere/Multi-Agent-QA-Orchestrator) was cloned into a separate review checkout and examined as a reference. Its current pipeline requires an LLM key and includes simulation support; GitHub returned no declared license. No source code from that repository was copied or executed. WebTrace retains its own key-free real-testing engine.

## Repository-inspired evidence features

See [REPOSITORY_REVIEW.md](REPOSITORY_REVIEW.md) for the exact upstream commit, modules reviewed, scope and independent implementation decisions. No upstream code was copied.

In New Test, choose the page discovery limit and optionally record a trace. Reports expose expandable page inventories, screenshot links, console/network filters, a trace download and issue guidance. Guidance is explicitly rule-based, not AI-generated root-cause analysis. Existing reports without these fields continue to work.

Verify these additions against a running backend:

```powershell
python scripts/verify_evidence.py
```

Results are recorded in `verification/evidence-results.json`. Open a downloaded trace with `python -m playwright show-trace <downloaded-zip-path>`. The diagnostic list omits request bodies/headers and redacts sensitive query parameter names; the native trace itself can include page and network data. Use synthetic data.
