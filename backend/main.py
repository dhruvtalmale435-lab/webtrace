"""WebTrace - FastAPI backend: Playwright test run + Visual Auditor + live logs.

Run from the PROJECT ROOT (the folder that contains /backend and /frontend):
    uvicorn backend.main:app --port 8000
"""
import asyncio
import copy
import os
import re
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
os.chdir(ROOT_DIR)  # the Visual Auditor uses paths relative to the project root
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from playwright.async_api import async_playwright
from pydantic import BaseModel, Field, HttpUrl

from backend.agents.visual_auditor import VisualAuditor
from backend.url_validator import validate_url
from backend import storage

try:  # optional: writes backend/reports/test_report.json + SUMMARY.md
    from backend.reporter import TestReporter
except Exception:  # pragma: no cover
    TestReporter = None

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
DATA_DIR = Path(os.getenv('WEBTRACE_DATA_DIR', str(BACKEND_DIR)))
SCREENSHOT_DIR = DATA_DIR / "screenshots"
REPORTS_DIR = DATA_DIR / "reports"
BASELINE_DIR = DATA_DIR / "baselines"
DEMO_DIR = BACKEND_DIR / "demo"
ARTIFACT_DIR = DATA_DIR / "artifacts"
for d in (SCREENSHOT_DIR, REPORTS_DIR, BASELINE_DIR, DEMO_DIR, ARTIFACT_DIR):
    d.mkdir(parents=True, exist_ok=True)

PORT = int(os.getenv("WEBTRACE_PORT", "8000"))
HEADLESS = os.getenv("WEBTRACE_HEADED", "0").lower() not in {"1", "true", "yes"}
SLOW_MO = int(os.getenv("WEBTRACE_SLOW_MO", "0") or 0)
VIEWPORT = {"width": 1280, "height": 800}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}

app = FastAPI(title="WebTrace - AI QA Agent", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
    ],
    # any localhost / 127.0.0.1 port (Vite may pick 5173, 5174, ...)
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/demo", StaticFiles(directory=str(DEMO_DIR)), name="demo")


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
class RunRequest(BaseModel):
    url: HttpUrl
    objective: str = Field(min_length=5, max_length=500)
    expected_selectors: list[str] = Field(default_factory=list, max_length=20)
    reset_baseline: bool = False
    prompt: str = Field(default="ui", pattern="^(ui|login|navigation|forms|assessment|submission|responsive|custom)$")
    authorized: bool = False
    crawl_pages: int = Field(default=1, ge=1, le=5)
    crawl_depth: int = Field(default=1, ge=0, le=2)
    capture_trace: bool = False


# --------------------------------------------------------------------------
# In-memory run store
# --------------------------------------------------------------------------
RUNS: dict[str, dict] = storage.load_runs()
for _state in RUNS.values():
    if _state["status"] in {"running", "queued"}:
        _state.update(status="error", stage="done", error="Execution interrupted by server restart; rerun this test.")
        storage.save_run(_state)
LOCK = threading.RLock()
EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="webtrace")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(state: dict, level: str, agent: str, message: str) -> None:
    """level: info | success | warning | error | bug"""
    with LOCK:
        state["logs"].append(
            {"ts": now_iso(), "level": level, "agent": agent, "message": str(message)}
        )


def update(state: dict, **fields) -> None:
    with LOCK:
        state.update(fields)
        storage.save_run(copy.deepcopy(state))


def short(exc) -> str:
    text = str(exc).strip()
    return (text.splitlines()[0] if text else type(exc).__name__)[:200]


def asset(path) -> str | None:
    return f"/screenshots/{Path(str(path)).name}" if path else None


def slug(url: str) -> str:
    p = urlsplit(url)
    raw = f"{p.hostname or 'site'}{p.path}".strip("/")
    import hashlib
    raw += "_" + hashlib.sha256(url.encode()).hexdigest()[:10]
    return re.sub(r"[^a-zA-Z0-9]+", "_", raw).strip("_").lower()[:80] or "site"


# --------------------------------------------------------------------------
# URL safety (blocks localhost/private IPs, except this server's /demo/ pages)
# --------------------------------------------------------------------------
def check_url(url: str) -> None:
    p = urlsplit(str(url))
    is_demo = (
        p.scheme == "http"
        and (p.hostname or "").lower() in {"localhost", "127.0.0.1"}
        and (p.port or 80) == PORT
        and p.path in {"/demo/assessment.html", "/demo/bad_ui.html", "/demo/missing.png", "/demo/assessment-help.html"}
        and not p.username and not p.password
        and ".." not in p.path
    )
    if not is_demo:
        validate_url(str(url))


# --------------------------------------------------------------------------
# Step 1: test plan (Gemini, with a built-in fallback)
# --------------------------------------------------------------------------
async def make_plan(state: dict, req: RunRequest) -> list[dict]:
    from backend.agents.planner import TestPlanner
    steps, limitations = TestPlanner.plan(req)
    update(state, plan_source="built-in", limitations=limitations)
    log(state, "success", "Test Planner", f"Created {len(steps)} executable checks.")
    return steps


# --------------------------------------------------------------------------
# Step 2: Playwright execution
# --------------------------------------------------------------------------
async def settle(page) -> None:
    try:
        await page.wait_for_load_state("load", timeout=5000)
    except Exception:
        pass


async def run_step(page, start_url: str, step: dict, index: int):
    action = step.get("action")
    target = step.get("target", "") or ""
    expected = step.get("expected", "") or ""
    value = step.get("value")

    if action == "navigate":
        dest = start_url if index == 1 else target
        check_url(dest)
        resp = await page.goto(dest, wait_until="domcontentloaded", timeout=30000)
        await settle(page)
        status = resp.status if resp else None
        if status and status >= 400:
            return False, f"{dest} returned HTTP {status}"
        return True, f"Opened {page.url}"

    if action in ("click", "fill"):
        try:
            loc = page.locator(target).first
            await loc.wait_for(state="visible", timeout=5000)
            if action == "click":
                await loc.click(timeout=10000)
            else:
                await loc.fill(value or "", timeout=10000)
        except Exception:
            try:  # controlled recovery: wait, then force once
                await asyncio.sleep(1.5)
                loc = page.locator(target).first
                if action == "click":
                    await loc.click(force=True, timeout=5000)
                else:
                    await loc.fill(value or "", force=True, timeout=5000)
            except Exception as exc2:
                return False, f"Could not {action} '{target}': {short(exc2)}"
        await settle(page)
        return True, f"{action} on '{target}' succeeded"

    if action == "verify":
        if target.lower() == "url":
            ok = expected in page.url
        else:
            try:
                await page.get_by_text(expected, exact=False).first.wait_for(state="visible", timeout=3000)
                ok = True
            except Exception:
                ok = False
        return ok, (f"Found: {expected}" if ok else f"Not found: {expected}")

    if action == "invalid_form":
        invalid = await page.locator("form").evaluate("(f) => !f.checkValidity()")
        return invalid, "Empty form rejects submission" if invalid else "Form accepts empty required fields"
    if action == "viewport":
        await page.set_viewport_size({"width": int(value), "height": 844})
        await page.wait_for_timeout(150)
        overflow = await page.evaluate("document.documentElement.scrollWidth > innerWidth + 2")
        return not overflow, f"Layout at {value}px: " + ("horizontal overflow detected" if overflow else "no horizontal overflow")
    if action == "inspect_navigation":
        links = await page.locator("a[href]").evaluate_all('(els) => els.map(e => e.getAttribute("href"))')
        invalid = [h for h in links if not h.strip() or h.strip() in {"#", "javascript:void(0)"}]
        return not invalid, f"{len(links)} links inspected; {len(invalid)} placeholder destinations"
    return False, f"Unsupported action: {action}"


async def run_steps(state, page, req, steps, short_id) -> None:
    total = len(steps)
    for i, step in enumerate(steps, start=1):
        label = step.get("target") if step.get("action") != "verify" else step.get("expected")
        log(state, "info", "Playwright", f"[{i}/{total}] {str(step.get('action')).upper()} - {label}")
        step_started = time.monotonic()
        try:
            ok, message = await run_step(page, str(req.url), step, i)
        except Exception as exc:
            ok, message = False, f"Step error: {short(exc)}"

        shot = None
        try:
            path = SCREENSHOT_DIR / f"{short_id}_step_{i}.png"
            try:
                await page.screenshot(path=str(path), full_page=True)
            except Exception:
                await page.screenshot(path=str(path))
            shot = asset(path)
        except Exception as exc:
            log(state, "warning", "Playwright", f"Screenshot failed: {short(exc)}")

        result = {
            "name": f"Step {i}: {step.get('action')}",
            "action": step.get("action"),
            "value": step.get("value"),
            "target": step.get("target"),
            "expected": step.get("expected"),
            "status": "passed" if ok else "failed",
            "message": message,
            "actual": message,
            "duration_ms": round((time.monotonic()-step_started)*1000),
            "screenshot_url": shot,
        }
        with LOCK:
            state["steps"].append(result)
        log(state, "success" if ok else "error", "Playwright",
            f"{result['name']} {'passed' if ok else 'FAILED'} - {message}")


# --------------------------------------------------------------------------
# Step 3: Visual Auditor (Akanksha)
# --------------------------------------------------------------------------
def resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else ROOT_DIR / p


async def run_audit(state, ctx, req, short_id) -> dict:
    url = str(req.url)
    log(state, "info", "Visual Auditor", f"Inspecting {url} ...")
    page = await ctx.new_page()
    js_errors: list[str] = []
    page.on("pageerror", lambda e: js_errors.append(str(e)))
    try:
        try:
            resp = await page.goto(url, wait_until="load", timeout=30000)
        except Exception:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        status = resp.status if resp else None
        try:
            await page.wait_for_load_state("networkidle", timeout=4000)
        except Exception:
            pass

        baseline = BASELINE_DIR / f"{slug(url)}.png"
        use_baseline = baseline.exists() and not req.reset_baseline

        auditor = VisualAuditor(screenshot_dir=SCREENSHOT_DIR, observe_ms=1000, reload_check=True)
        result = await auditor.audit_page(
            page,
            expected_selectors=req.expected_selectors or None,
            js_errors=js_errors,
            page_status=status,
            baseline_screenshot=str(baseline) if use_baseline else None,
        )

        original = Path(result["screenshot"])
        annotated = Path(result["annotated_screenshot"])

        regression = None
        if use_baseline:
            base_copy = SCREENSHOT_DIR / f"{short_id}_baseline.png"
            shutil.copyfile(baseline, base_copy)
            regression = dict(result.get("visual_regression") or {})
            regression["baseline_url"] = asset(base_copy)
            regression["current_url"] = asset(original)
            diff_src = regression.get("diff_image_path")
            if diff_src and resolve(diff_src).exists():
                diff_copy = SCREENSHOT_DIR / f"{short_id}_visual_diff.png"
                shutil.copyfile(resolve(diff_src), diff_copy)
                regression["diff_image_url"] = asset(diff_copy)
        else:
            shutil.copyfile(original, baseline)
            log(state, "info", "Visual Auditor",
                "Baseline saved for this URL. Run the same URL again to see a visual diff.")

        issues = []
        for n, raw in enumerate(result.get("issues", []), start=1):
            issues.append({
                "id": raw.get("id", n),
                "category": raw.get("category", "unknown"),
                "severity": raw.get("severity", "medium"),
                "description": raw.get("description", ""),
                "element": raw.get("element"),
                "confidence": raw.get("confidence"),
            })
        issues.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 9))

        for issue in issues:
            high = issue["severity"] == "high"
            log(state, "bug" if high else "warning", "Visual Auditor",
                f"[{'Bug' if high else 'Flaw'}] {issue['category']} - {issue['description']}")

        by_sev: dict[str, int] = {}
        by_cat: dict[str, int] = {}
        for issue in issues:
            by_sev[issue["severity"]] = by_sev.get(issue["severity"], 0) + 1
            by_cat[issue["category"]] = by_cat.get(issue["category"], 0) + 1

        return {
            "status": "completed",
            "page_url": result.get("page_url", url),
            "http_status": status,
            "issues": issues,
            "issues_found": len(issues),
            "by_severity": by_sev,
            "by_category": by_cat,
            "javascript_errors": result.get("javascript_errors", []),
            "screenshot_url": asset(original),
            "annotated_screenshot_url": asset(annotated),
            "visual_regression": regression,
            "baseline_created": not use_baseline,
            "error": None,
        }
    finally:
        try:
            await page.close()
        except Exception:
            pass


# --------------------------------------------------------------------------
# Step 4: report + pipeline
# --------------------------------------------------------------------------
def build_summary(state: dict, audit: dict | None) -> dict:
    steps = state["steps"]
    failed = sum(1 for s in steps if s["status"] == "failed")
    issues = (audit or {}).get("issues_found", 0)
    verdict = "error" if audit is None or audit.get("status") == "error" else "failed" if failed else ("issues_found" if issues else "passed")
    return {
        "steps_total": len(steps),
        "steps_passed": len(steps) - failed,
        "steps_failed": failed,
        "issues_total": issues,
        "by_severity": (audit or {}).get("by_severity", {}),
        "by_category": (audit or {}).get("by_category", {}),
        "verdict": verdict,
    }


def write_report_files(state: dict, audit: dict | None) -> None:
    if not TestReporter:
        return
    r = TestReporter()
    for s in state["steps"]:
        r.add_test_result(s["name"], "PASS" if s["status"] == "passed" else "FAIL",
                          s["message"], evidence_path=s["screenshot_url"])
    for i in (audit or {}).get("issues", []):
        r.add_visual_bug(str(i.get("element") or i["category"]), i["description"],
                         str(i["severity"]).capitalize())
    r.generate_json_report(str(REPORTS_DIR / "test_report.json"))
    r.generate_markdown_report(str(REPORTS_DIR / "SUMMARY.md"))


async def pipeline(state: dict, req: RunRequest) -> None:
    short_id = state["run_id"][:8]
    t0 = time.monotonic()
    audit = None
    try:
        update(state, status="running", stage="planning", started_at=now_iso())
        log(state, "info", "Orchestrator", f"Run {short_id} started: {req.url}")
        log(state, "info", "Orchestrator", f"Objective: {req.objective}")

        steps = await make_plan(state, req)
        update(state, plan=steps, stage="exploring")

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
            ctx = None
            try:
                ctx = await browser.new_context(viewport=VIEWPORT, device_scale_factor=1, accept_downloads=False, service_workers="block")
                from backend.agents.diagnostics import BrowserDiagnostics
                from backend.agents.explorer import origin
                def record_diagnostic(event):
                    with LOCK:
                        if len(state['diagnostics']) < 150:
                            state['diagnostics'].append(event)
                        else:
                            state['diagnostics_dropped'] += 1
                BrowserDiagnostics(record_diagnostic).attach(ctx)
                if req.capture_trace:
                    await ctx.tracing.start(screenshots=True, snapshots=True, sources=False)
                async def guard(route):
                    try:
                        if route.request.method not in {"GET", "HEAD"}:
                            return await route.abort()
                        if route.request.resource_type == 'document' and origin(route.request.url) != origin(str(req.url)):
                            raise ValueError('Navigation outside the authorized origin is blocked')
                        await asyncio.to_thread(check_url, route.request.url)
                        await route.continue_()
                    except Exception:
                        await route.abort()
                await ctx.route("**/*", guard)
                await ctx.route_web_socket("**/*", lambda ws: ws.close())
                ctx.set_default_timeout(5000)
                page = await ctx.new_page()
                log(state, "info", "Playwright", "Chromium started.")
                from backend.agents.explorer import inspect_page, discover
                response = await page.goto(str(req.url), wait_until="domcontentloaded", timeout=30000)
                observation = await inspect_page(page)
                def discovered(record):
                    with LOCK:
                        state['discovery'].append(record)
                    log(state, 'info', 'Explorer', f"{record['status']}: {record['url']}")
                await discover(ctx, page, str(req.url), req.crawl_pages, req.crawl_depth, check_url, SCREENSHOT_DIR, state['run_id'], discovered, response.status if response else None)
                unavailable = sum(p['status'] in {'blocked', 'error'} for p in state['discovery'])
                if unavailable:
                    state['limitations'].append(f'Discovery could not inspect {unavailable} page(s). Review page discovery errors; the verdict covers executed checks only.')
                update(state, exploration=observation, stage="testing")
                log(state, "success", "Explorer", f"Inspected {len(state['discovery'])} page(s); start page has {observation['links']} links and {observation['forms']} forms.")
                await run_steps(state, page, req, steps, short_id)

                update(state, stage="auditing")
                try:
                    audit = await run_audit(state, ctx, req, short_id)
                except Exception as exc:
                    log(state, "error", "Visual Auditor", f"Audit failed: {short(exc)}")
                    audit = {"status": "error", "issues": [], "issues_found": 0,
                             "by_severity": {}, "by_category": {}, "javascript_errors": [],
                             "screenshot_url": None, "annotated_screenshot_url": None,
                             "visual_regression": None, "error": short(exc)}
            finally:
                if req.capture_trace and ctx is not None:
                    try:
                        await ctx.tracing.stop(path=str(ARTIFACT_DIR / (state['run_id'] + '.zip')))
                        update(state, artifacts={'trace_url': '/api/tests/' + state['run_id'] + '/artifacts/trace'})
                    except Exception as exc:
                        log(state, 'warning', 'Reporter', f'Trace capture failed: {short(exc)}')
                await browser.close()

        update(state, visual_audit=audit, stage="reporting")
        summary = build_summary(state, audit)
        try:
            write_report_files(state, audit)
        except Exception as exc:
            log(state, "warning", "Reporter", f"Report files not written: {short(exc)}")

        lvl = {"passed": "success", "issues_found": "warning"}.get(summary["verdict"], "error")
        log(state, lvl, "Reporter",
            f"Done: {summary['steps_passed']}/{summary['steps_total']} steps passed, "
            f"{summary['issues_total']} visual issue(s).")
        update(state, status="error" if summary["verdict"] == "error" else "running", stage="reporting", summary=summary)
    except asyncio.CancelledError:
        update(state, status='error', stage='done', error='Execution exceeded 120 seconds', visual_audit=audit, summary=build_summary(state, audit))
        raise
    except Exception as exc:
        log(state, "error", "Orchestrator", f"Run failed: {short(exc)}")
        update(state, status="error", stage="done", error=short(exc),
               visual_audit=audit, summary=build_summary(state, audit))
    finally:
        update(state, finished_at=now_iso(), duration_seconds=round(time.monotonic() - t0, 1))
        with LOCK:
            if state['status'] != 'error':
                state.update(status='completed', stage='done')
            storage.finalize(state)


def run_in_new_loop(coro) -> None:
    """Own event loop per run: Playwright needs the Proactor loop on Windows."""
    loop = asyncio.ProactorEventLoop() if sys.platform == "win32" else asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()


def start_run(req: RunRequest) -> dict:
    state = {
        "run_id": str(uuid4()), "status": "queued", "stage": "queued",
        "url": str(req.url), "objective": req.objective, "prompt": req.prompt, "request": req.model_dump(mode="json"),
        "created_at": now_iso(), "started_at": None, "finished_at": None,
        "duration_seconds": None, "logs": [], "plan": None, "plan_source": None,
        "steps": [], "visual_audit": None, "summary": None, "error": None,
        "discovery": [], "diagnostics": [], "diagnostics_dropped": 0, "artifacts": {},
    }
    with LOCK:
        RUNS[state["run_id"]] = state
        storage.save_run(state)

    def job():
        try:
            run_in_new_loop(asyncio.wait_for(pipeline(state, req), timeout=120))
        except Exception as exc:
            log(state, "error", "Orchestrator", f"Fatal: {short(exc)}")
            update(state, status="error", stage="done", error="Execution exceeded 120 seconds" if isinstance(exc, TimeoutError) else short(exc))

    EXECUTOR.submit(job)
    return state


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------
@app.get("/")
def home():
    index = ROOT_DIR / "frontend" / "dist" / "index.html"
    if index.exists(): return FileResponse(index)
    return {"message": "WebTrace API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "WebTrace backend"}


def _create(req: RunRequest):
    if not req.authorized:
        raise HTTPException(status_code=400, detail="Confirm you are authorized to test this website.")
    try:
        check_url(str(req.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    with LOCK:
        if sum(r['status'] in {'queued', 'running'} for r in RUNS.values()) >= 2:
            raise HTTPException(status_code=429, detail="Two tests are already active. Wait for a run to finish.")
        state = start_run(req)
    return {"run_id": state["run_id"], "status": "queued",
            "message": "Test started. Poll GET /api/tests/{run_id} for live results."}


@app.post("/api/tests")
def create_test(req: RunRequest):
    return _create(req)


@app.post("/run-test")  # alias for the old frontend api.js
def run_test(req: RunRequest):
    return _create(req)


@app.get("/api/tests")
def list_tests(limit: int = 20):
    with LOCK:
        runs = sorted(RUNS.values(), key=lambda r: r["created_at"], reverse=True)[:max(1, min(limit, 500))]
        return [{
            "run_id": r["run_id"], "status": r["status"], "stage": r["stage"],
            "url": r["url"], "objective": r["objective"], "created_at": r["created_at"],
            "duration_seconds": r["duration_seconds"],
            "verdict": (r["summary"] or {}).get("verdict"),
            "issues_total": (r["summary"] or {}).get("issues_total"),
        } for r in runs]


@app.get("/api/tests/{run_id}")
def get_test(run_id: str):
    with LOCK:
        state = RUNS.get(run_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Test run not found")
        return copy.deepcopy(state)


@app.get("/api/tests/{run_id}/report")
def get_test_report(run_id: str):
    return get_test(run_id)


@app.get("/api/report/json")
def latest_json_report():
    p = REPORTS_DIR / "test_report.json"
    if p.exists():
        return FileResponse(str(p), media_type="application/json")
    return {"error": "Report not found. Run a test first."}


@app.get("/api/report/summary")
def latest_markdown_report():
    p = REPORTS_DIR / "SUMMARY.md"
    if p.exists():
        return FileResponse(str(p), media_type="text/markdown")
    return {"error": "Summary not found."}

from backend.api_extensions import register
register(app, RUNS, LOCK, _create, RunRequest, SCREENSHOT_DIR, ARTIFACT_DIR)

# Serve the built SPA with the API from one origin.
_dist = ROOT_DIR / "frontend" / "dist"
if (_dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(_dist / "assets")), name="assets")

@app.get("/{path:path}")
def frontend_fallback(path: str):
    if path.startswith(("api/", "screenshots/", "demo/")):
        raise HTTPException(404, "Not found")
    index = _dist / "index.html"
    if index.exists(): return FileResponse(index)
    raise HTTPException(404, "Build frontend first with npm run build")
