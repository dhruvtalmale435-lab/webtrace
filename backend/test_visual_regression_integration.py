import asyncio
from pathlib import Path

from playwright.async_api import async_playwright
from backend.agents.visual_auditor import VisualAuditor


async def main():
    screenshot_dir = Path("backend/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    baseline_path = screenshot_dir / "integration_baseline.png"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        page = await browser.new_page(
            viewport={"width": 1280, "height": 720},
            device_scale_factor=1,
        )

        await page.set_content("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Visual Regression Integration Test</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        padding: 20px;
                    }

                    #test-box {
                        width: 300px;
                        height: 150px;
                        background-color: blue;
                    }
                </style>
            </head>
            <body>
                <h1>Visual Regression Test</h1>
                <p>Testing screenshot comparison.</p>
                <div id="test-box"></div>
            </body>
            </html>
        """)

        await page.screenshot(
            path=str(baseline_path),
            full_page=True,
        )

        print("Baseline screenshot created:", baseline_path)

        await page.locator("#test-box").evaluate("""
            element => {
                element.style.backgroundColor = "red";
                element.style.width = "450px";
            }
        """)

        auditor = VisualAuditor(
            screenshot_dir=str(screenshot_dir),
        )

        report = await auditor.audit_page(
            page,
            baseline_screenshot=str(baseline_path),
        )

        regression = report.get("visual_regression")

        print("\nVISUAL REGRESSION INTEGRATION TEST")
        print("=" * 50)
        print("Audit status:", report["status"])
        print("UI issues found:", report["issues_found"])
        print("Visual regression result:", regression)

        assert regression is not None, (
            "Visual regression result was not included in the report."
        )

        assert regression.get("visual_changes_detected") is True, (
            "The visual change was not detected."
        )

        assert regression.get("difference_percentage", 0) > 0, (
            "The difference percentage should be greater than zero."
        )

        assert Path(regression["diff_image_path"]).is_file(), (
            "The difference image was not created."
        )

        print("\nPASS: Visual regression was integrated successfully.")
        print("PASS: The visual change was detected.")
        print("PASS: The difference image was generated.")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())