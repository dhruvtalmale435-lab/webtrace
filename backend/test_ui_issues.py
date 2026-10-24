import asyncio
import json

from playwright.async_api import async_playwright
from backend.agents.visual_auditor import VisualAuditor


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        page = await browser.new_page(
            viewport={"width": 1280, "height": 720}
        )

        # Create a webpage containing both faulty and valid UI elements.
        await page.set_content("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>WebTrace UI Test</title>

                <style>
                    body {
                        font-family: Arial, sans-serif;
                        padding: 20px;
                    }

                    .wide-content {
                        width: 1600px;
                    }

                    .hidden-message {
                        display: none;
                    }
                </style>
            </head>

            <body>
                <h1>WebTrace UI Test</h1>

                <!-- Valid button with visible text -->
                <button id="login">Login</button>

                <!-- Invalid button without an accessible name -->
                <button id="empty-button"></button>

                <!-- Valid icon button with an accessible name -->
                <button id="icon-button" aria-label="Open settings">
                    <svg
                        width="16"
                        height="16"
                        aria-hidden="true"
                    >
                        <circle cx="8" cy="8" r="6"></circle>
                    </svg>
                </button>

                <!-- Intentionally hidden element -->
                <p class="hidden-message">
                    This message is hidden.
                </p>

                <!-- Intentionally overflowing content -->
                <div class="wide-content">
                    This content is wider than the viewport.
                </div>

                <!-- Intentionally broken image -->
                <img
                    id="broken-image"
                    src="missing-image.png"
                    alt="Broken product image"
                >

                <!-- Valid image stored directly in the HTML -->
                <img
                    id="working-image"
                    alt="Working test image"
                    src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect width='100' height='100' fill='green'/%3E%3C/svg%3E"
                >
            </body>
            </html>
        """)

        # Wait for the browser to finish processing the images.
        await page.wait_for_function("""
            () => {
                const image = document.querySelector("#working-image");
                return image && image.complete;
            }
        """)

        print("=" * 60)
        print("WEBTRACE VISUAL AUDITOR TEST")
        print("=" * 60)

        print("Page title:", await page.title())
        print("H1 count:", await page.locator("h1").count())
        print("Login button count:", await page.locator("#login").count())

        # Verify the test setup.
        working_image_loaded = await page.locator(
            "#working-image"
        ).evaluate(
            "(img) => img.complete && img.naturalWidth > 0"
        )

        broken_image_loaded = await page.locator(
            "#broken-image"
        ).evaluate(
            "(img) => img.complete && img.naturalWidth > 0"
        )

        print("\nTEST PAGE VALIDATION")
        print("-" * 60)
        print("Working image loaded:", working_image_loaded)
        print("Broken image loaded:", broken_image_loaded)

        # Run the Visual Auditor.
        auditor = VisualAuditor(reload_check=False)

        results = await auditor.audit_page(
            page,
            expected_selectors=[
                "h1",
                "#login",
                "#missing-button",
                ".hidden-message"
            ]
        )

        print("\nVISUAL AUDITOR REPORT")
        print("-" * 60)
        print(json.dumps(results, indent=4))

       
        # Collect the detected issues.
        issues = results.get("issues", [])

        issue_types = {
            issue.get("category")
            for issue in issues
        }

        missing_element_detected = any(
            issue.get("category") == "missing_element"
            and issue.get("element") == "#missing-button"
            for issue in issues
        )

        hidden_element_detected = any(
            issue.get("category") == "hidden_element"
            and issue.get("element") == ".hidden-message"
            for issue in issues
        )

        overflow_detected = (
            "horizontal_overflow" in issue_types
        )

        empty_button_detected = any(
            issue.get("category") == "empty_button"
            and issue.get("element") == "button#empty-button"
            for issue in issues
        )

        broken_image_detected = any(
            issue.get("category") == "broken_image"
            and issue.get("element") == "img#broken-image"
            for issue in issues
        )

        working_image_incorrectly_reported = any(
            issue.get("category") == "broken_image"
            and issue.get("element") == "img#working-image"
            for issue in issues
        )

        accessible_button_incorrectly_reported = any(
            issue.get("category") == "empty_button"
            and issue.get("element") == "button#icon-button"
            for issue in issues
        )


        # Define expected outcomes.
        tests = [
            (
                "Missing element detected",
                missing_element_detected
            ),
            (
                "Hidden element detected",
                hidden_element_detected
            ),
            (
                "Horizontal overflow detected",
                overflow_detected
            ),
            (
                "Empty button detected",
                empty_button_detected
            ),
            (
                "Broken image detected",
                broken_image_detected
            ),
            (
                "Working image not incorrectly reported",
                not working_image_incorrectly_reported
            ),
            (
                "Accessible button not incorrectly reported",
                not accessible_button_incorrectly_reported
            ),
        ]

        # Display a readable summary.
        print("\nTEST CHECK SUMMARY")
        print("=" * 60)

        passed = 0
        failed = 0

        for test_name, success in tests:
            status = "PASS" if success else "FAIL"

            print(f"{status}: {test_name}")

            if success:
                passed += 1
            else:
                failed += 1

        print("-" * 60)
        print(f"Tests passed: {passed}/{len(tests)}")
        print(f"Tests failed: {failed}/{len(tests)}")
        print("Issues reported by auditor:", results.get("issues_found"))

        print("Screenshot:", results.get("screenshot"))
        print("=" * 60)

        await browser.close()

        # Exit with a failure code if any check failed.
        if failed:
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())