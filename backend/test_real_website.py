import asyncio
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from backend.agents.visual_auditor import VisualAuditor


# ============================================================
# CONFIGURATION
# ============================================================

HEADLESS = False

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 800

NAVIGATION_TIMEOUT_MS = 60000
RENDER_WAIT_MS = 2000

IGNORE_HTTPS_ERRORS = False


# ============================================================
# URL VALIDATION
# ============================================================

def normalize_url(raw_url: str) -> str:
    """Validate and normalize a website URL."""

    website_url = raw_url.strip()

    if not website_url:
        raise ValueError("Website URL cannot be empty.")

    if not website_url.startswith(("https://", "http://")):
        website_url = "https://" + website_url

    parsed_url = urlparse(website_url)

    if (
        parsed_url.scheme not in ("http", "https")
        or not parsed_url.hostname
        or any(char.isspace() for char in parsed_url.netloc)
        or parsed_url.username is not None
        or parsed_url.password is not None
    ):
        raise ValueError(
            "Invalid URL. Enter a valid website address, "
            "for example https://example.com"
        )

    return website_url


# ============================================================
# MAIN AUDIT FUNCTION
# ============================================================

async def main():
    print("=" * 60)
    print("WEBTRACE - REAL WEBSITE VISUAL AUDITOR")
    print("=" * 60)

    try:
        raw_url = input("Enter website URL: ")
        website_url = normalize_url(raw_url)

    except ValueError as error:
        print(f"\nInvalid URL: {error}")
        return

    auditor = VisualAuditor()
    browser = None
    context = None

    javascript_errors = []
    audit_results = None

    try:
        async with async_playwright() as playwright:
            # Launch Chromium.
            browser = await playwright.chromium.launch(
                headless=HEADLESS
            )

            # Configure browser context.
            context = await browser.new_context(
                viewport={
                    "width": VIEWPORT_WIDTH,
                    "height": VIEWPORT_HEIGHT,
                },
                ignore_https_errors=IGNORE_HTTPS_ERRORS,
            )

            page = await context.new_page()

            # Collect uncaught JavaScript runtime errors.
            def record_javascript_error(error):
                javascript_errors.append(str(error))

            page.on("pageerror", record_javascript_error)

            print(f"\nOpening website: {website_url}")
            print("Please wait while the website loads...\n")

            response = None

            try:
                response = await page.goto(
                    website_url,
                    wait_until="domcontentloaded",
                    timeout=NAVIGATION_TIMEOUT_MS,
                )

            except PlaywrightTimeoutError:
                print(
                    "Warning: Navigation timed out. "
                    "Continuing if the page is available."
                )

            # Check whether navigation produced a usable page.
            if page.is_closed():
                raise RuntimeError(
                    "The browser page closed before the audit could run."
                )

            # Allow the page to render.
            await page.wait_for_timeout(RENDER_WAIT_MS)

            page_title = await page.title()
            final_url = page.url
            page_status = (
                response.status if response is not None else None
            )

            print(f"Page title: {page_title}")
            print(f"Final URL: {final_url}")
            print(f"HTTP status: {page_status}")
            print("\nRunning Visual Auditor...\n")

            # Run the visual audit.
            audit_results = await auditor.audit_page(
                page,
                expected_selectors=[],
                js_errors=javascript_errors,
                page_status=page_status,
            )

            # Add website and navigation information to the report.
            if not isinstance(audit_results, dict):
                raise TypeError(
                    "VisualAuditor.audit_page() must return a dictionary."
                )

            audit_results["website_url"] = website_url
            audit_results["final_url"] = final_url
            audit_results["page_title"] = page_title
            audit_results["page_status"] = page_status
            audit_results["javascript_errors"] = javascript_errors

            # Save the JSON report.
            report_dir = Path("backend") / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )

            report_path = report_dir / f"audit_report_{timestamp}.json"

            with report_path.open("w", encoding="utf-8") as report_file:
                json.dump(
                    audit_results,
                    report_file,
                    indent=4,
                    ensure_ascii=False,
                    default=str,
                )

            # Print the complete report.
            print("=" * 60)
            print("AUDIT REPORT")
            print("=" * 60)

            print(
                json.dumps(
                    audit_results,
                    indent=4,
                    ensure_ascii=False,
                    default=str,
                )
            )

            # Print a concise summary.
            issues = audit_results.get("issues", [])
            issue_count = audit_results.get(
                "issues_found", len(issues)
            )

            print("\n" + "=" * 60)
            print("AUDIT SUMMARY")
            print("=" * 60)

            print(f"Website: {final_url}")
            print(f"HTTP status: {page_status}")
            print(f"Issues found: {issue_count}")
            print(f"JavaScript errors: {len(javascript_errors)}")
            print(f"JSON report: {report_path}")

            screenshot_path = audit_results.get("screenshot")
            annotated_path = audit_results.get("annotated_screenshot")

            if screenshot_path:
                print(f"Original screenshot: {screenshot_path}")

            if annotated_path:
                print(f"Annotated screenshot: {annotated_path}")

            if issues:
                print("\nDetected issues:")

                for index, issue in enumerate(issues, start=1):
                    if isinstance(issue, dict):
                        category = issue.get(
                            "category",
                            issue.get("type", "UI issue"),
                        )
                        description = issue.get(
                            "description",
                            issue.get(
                                "message",
                                issue.get("selector", "No description provided"),
                            ),
                        )
                        print(f"{index}. [{category}] {description}")
                    else:
                        print(f"{index}. {issue}")

            else:
                print("\nNo UI issues were reported by the auditor.")

            if javascript_errors:
                print("\nJavaScript runtime errors:")

                for error in javascript_errors:
                    print(f"- {error}")

            print("\nAudit completed.")

    except Exception as error:
        print(f"\nAudit failed: {type(error).__name__}: {error}")

    finally:
        if context is not None:
            try:
                await context.close()
            except Exception:
                pass

        if browser is not None:
            try:
                await browser.close()
            except Exception:
                pass


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())
