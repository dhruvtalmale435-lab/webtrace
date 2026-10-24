"""
Runs the Visual Auditor on a local page with KNOWN bugs.

Run from the project root:
    python -m backend.test_demo_page

Expected bugs: missing element, hidden element, broken image, empty button,
horizontal overflow. Warnings: missing alt, unlabeled field/checkbox,
empty link, possible overlap.
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

from backend.agents.visual_auditor import VisualAuditor

DEMO_PAGE = Path(__file__).parent / "demo" / "bad_ui.html"
EXPECTED_SELECTORS = ["#missing-button", ".hidden-message"]
EXPECTED_BUGS = {
    "missing_element",
    "hidden_element",
    "broken_image",
    "empty_button",
    "horizontal_overflow",
}


async def main():
    url = DEMO_PAGE.resolve().as_uri()
    print(f"Auditing demo page: {url}\n")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        js_errors = []
        page.on("pageerror", lambda error: js_errors.append(str(error)))

        response = await page.goto(url, wait_until="load")
        status = response.status if response and response.status else 200

        result = await VisualAuditor().audit_page(
            page,
            expected_selectors=EXPECTED_SELECTORS,
            js_errors=js_errors,
            page_status=status,
        )

        await browser.close()

    reports = Path("backend/reports")
    reports.mkdir(parents=True, exist_ok=True)
    report_path = reports / f"demo_report_{datetime.now():%Y%m%d_%H%M%S}.json"
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Status: {result['status']}")
    print(f"Bugs: {result.get('bugs_found')}   Warnings: {result.get('warnings_found')}\n")

    for issue in result["issues"]:
        print(f"{issue['id']}. [{issue['type'].upper()}] {issue['category']} - {issue['detail']}")

    found = {i["category"] for i in result["issues"] if i["type"] == "bug"}
    missing = EXPECTED_BUGS - found
    print("\nAll expected bugs detected." if not missing else f"\nNOT detected: {sorted(missing)}")

    print(f"\nAnnotated screenshot: {result['annotated_screenshot']}")
    print(f"JSON report: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())