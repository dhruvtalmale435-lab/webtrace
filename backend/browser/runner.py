"""Low-level Playwright wrapper (browser / context / page / screenshots).

Merged from two branches:
  * HEAD   - start_browser / capture_screenshot / close_browser (used by BrowserTester)
  * a26ed30 - batch run(plan) helper
Both are kept, so nothing that used either version breaks.
"""
import os
from pathlib import Path

from playwright.async_api import async_playwright

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SCREENSHOT_DIR = BACKEND_DIR / "screenshots"

DEFAULT_VIEWPORT = {"width": 1280, "height": 800}


class BrowserRunner:
    def __init__(self, screenshot_dir=None, viewport=None):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.screenshot_dir = Path(screenshot_dir or DEFAULT_SCREENSHOT_DIR)
        self.viewport = viewport or DEFAULT_VIEWPORT
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    async def start_browser(self, headless: bool = True, slow_mo: int = 0):
        """Launch Chromium and open the first page."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
        if not self.browser:
            self.browser = await self.playwright.chromium.launch(
                headless=headless, slow_mo=slow_mo
            )
            # device_scale_factor=1 keeps screenshots and auditor boxes aligned.
            self.context = await self.browser.new_context(
                viewport=self.viewport, device_scale_factor=1
            )
            self.page = await self.context.new_page()
        return self.page

    async def new_page(self):
        """Extra page in the same browser (used by the Visual Auditor)."""
        if not self.context:
            raise RuntimeError("Browser is not started.")
        return await self.context.new_page()

    async def capture_screenshot(self, step_name: str, page=None) -> str:
        """Save a screenshot and return its file path ('' if no page)."""
        page = page or self.page
        if not page:
            return ""
        file_path = self.screenshot_dir / f"{step_name}.png"
        try:
            await page.screenshot(path=str(file_path), full_page=True)
        except Exception:
            # Some pages cannot be captured full-page; fall back to the viewport.
            await page.screenshot(path=str(file_path), full_page=False)
        return str(file_path)

    async def close_browser(self):
        """Close everything. Safe to call more than once."""
        try:
            if self.browser:
                await self.browser.close()
        finally:
            self.browser = None
            self.context = None
            self.page = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

    async def run(self, plan):
        """Batch-execute a TestPlan and return a list of step result dicts."""
        results = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                for index, step in enumerate(plan.steps, start=1):
                    action = step.action
                    target = step.target
                    expected = step.expected
                    value = getattr(step, "value", None)

                    try:
                        if action == "navigate":
                            await page.goto(target, wait_until="domcontentloaded")
                            message = f"Opened {page.url}"

                        elif action == "click":
                            await page.locator(target).first.click(timeout=10000)
                            message = f"Clicked {target}"

                        elif action == "fill":
                            await page.locator(target).first.fill(
                                value or "", timeout=10000
                            )
                            message = f"Filled {target}"

                        elif action == "verify":
                            if target == "text":
                                found = (
                                    await page.get_by_text(expected, exact=False).count()
                                    > 0
                                )
                                if not found:
                                    raise AssertionError(f"Text not found: {expected}")
                                message = f"Text found: {expected}"

                            elif target == "url":
                                if expected not in page.url:
                                    raise AssertionError(
                                        f"Expected URL to contain {expected}; "
                                        f"actual URL: {page.url}"
                                    )
                                message = f"URL verified: {page.url}"

                            else:
                                raise ValueError(
                                    f"Unsupported verification target: {target}"
                                )
                        else:
                            raise ValueError(f"Unsupported action: {action}")

                        status = "passed"

                    except Exception as exc:
                        status = "failed"
                        message = str(exc)

                    try:
                        await page.screenshot(
                            path=str(self.screenshot_dir / f"step_{index}.png")
                        )
                    except Exception:
                        pass

                    results.append(
                        {
                            "name": f"Step {index}: {action}",
                            "status": status,
                            "message": message,
                        }
                    )

            finally:
                await browser.close()

        return results
