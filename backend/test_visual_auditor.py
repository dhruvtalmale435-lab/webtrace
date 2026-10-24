import asyncio
import json

from playwright.async_api import async_playwright
from backend.agents.visual_auditor import VisualAuditor


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={
            "width": 1280,
            "height": 720
        })

        # Create a sample page with one missing expected element.
        await page.set_content("""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        padding: 30px;
                    }

                    h1 {
                        color: navy;
                    }
                </style>
            </head>
            <body>
                <h1>WebTrace Visual Auditor Test</h1>
                <p>This is a sample webpage.</p>
                <button id="checkout">Checkout</button>
            </body>
            </html>
        """)

        auditor = VisualAuditor()

        results = await auditor.audit_page(
            page,
            expected_selectors=[
                "h1",
                "#checkout",
                "#missing-button"
            ]
        )

        print(json.dumps(results, indent=4))

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())