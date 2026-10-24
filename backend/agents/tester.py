"""Playwright Tester agent (Gunjan & Vruddhi).

Merged from two branches:
  * HEAD    - BrowserRunner based, controlled-recovery, element_visible assertion
  * a26ed30 - robust navigation, case-insensitive text verification, fill support
The public API is unchanged:
    start / navigate_to / execute_action / verify_assertion /
    capture_screenshot / close, plus `tester.runner.capture_screenshot(name)`.
"""
import asyncio
import os

from backend.browser.runner import BrowserRunner


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class BrowserTester:
    def __init__(self, log=None, headless=None, screenshot_dir=None):
        """
        log      : optional callable(level, message) - receives live log lines
                   (levels: info, success, warning, error).
        headless : True/False. Default: headless unless WEBTRACE_HEADED=1
                   (handy for a live demo where the audience watches the browser).
        """
        self.runner = BrowserRunner(screenshot_dir=screenshot_dir)
        self.page = None
        self.headless = (
            headless if headless is not None else not _env_flag("WEBTRACE_HEADED")
        )
        self.slow_mo = int(os.getenv("WEBTRACE_SLOW_MO", "0") or 0)
        self._log = log or (lambda level, message: print(f"[{level}] {message}"))

    def log(self, level: str, message: str):
        try:
            self._log(level, message)
        except Exception:
            pass

    async def start(self):
        self.page = await self.runner.start_browser(
            headless=self.headless, slow_mo=self.slow_mo
        )
        mode = "headless" if self.headless else "visible window"
        self.log("info", f"Chromium started ({mode}).")

    async def navigate_to(self, url: str):
        """Open a URL. Returns the HTTP status code (or None)."""
        if not self.page:
            await self.start()

        response = await self.page.goto(
            str(url), wait_until="domcontentloaded", timeout=30000
        )
        try:
            await self.page.wait_for_load_state("load", timeout=8000)
        except Exception:
            pass  # slow assets must not fail the navigation itself

        status = response.status if response else None
        try:
            title = await self.page.title()
        except Exception:
            title = ""
        self.log("info", f"Opened {self.page.url} (HTTP {status}, title: '{title}')")
        return status

    async def _settle(self):
        """Give the page a moment to finish any navigation a click triggered."""
        try:
            await self.page.wait_for_load_state("load", timeout=5000)
        except Exception:
            pass

    async def execute_action(self, action_type: str, selector: str, value: str = None):
        """click / fill / type / scroll on the first element matching `selector`."""
        try:
            locator = self.page.locator(selector).first
            await locator.wait_for(state="visible", timeout=5000)

            if action_type == "click":
                await locator.click(timeout=10000)
            elif action_type in ("type", "fill"):
                await locator.fill(value or "", timeout=10000)
            elif action_type == "scroll":
                await locator.scroll_into_view_if_needed()
            else:
                self.log("error", f"Unknown action type: {action_type}")
                return False

            await self._settle()
            self.log("success", f"{action_type} on '{selector}' succeeded.")
            return True

        except Exception as exc:
            first_line = str(exc).strip().splitlines()[0] if str(exc).strip() else repr(exc)
            self.log(
                "warning",
                f"{action_type} on '{selector}' failed ({first_line}). "
                "Trying controlled recovery...",
            )
            return await self.controlled_recovery(action_type, selector, value)

    async def verify_assertion(
        self, assertion_type: str, expected_value: str, selector: str = None
    ):
        """text_visible | url_contains | element_visible"""
        try:
            passed = False
            if assertion_type == "text_visible":
                body_text = await self.page.locator("body").inner_text()
                passed = expected_value.lower() in body_text.lower()
                if not passed:
                    html = await self.page.content()
                    passed = expected_value.lower() in html.lower()
            elif assertion_type == "url_contains":
                passed = expected_value in self.page.url
            elif assertion_type == "element_visible" and selector:
                passed = await self.page.locator(selector).first.is_visible()

            if passed:
                self.log("success", f"Assertion passed: {assertion_type} -> '{expected_value}'")
            else:
                self.log("warning", f"Assertion failed: {assertion_type} -> '{expected_value}' not found")
            return passed

        except Exception as exc:
            self.log("error", f"Assertion error: {exc}")
            return False

    async def controlled_recovery(self, action_type: str, selector: str, value: str = None) -> bool:
        """One forced retry after a short wait (covers overlays / slow rendering)."""
        try:
            await asyncio.sleep(1.5)
            locator = self.page.locator(selector).first
            if action_type == "click":
                await locator.click(force=True, timeout=5000)
            elif action_type in ("type", "fill"):
                await locator.fill(value or "", force=True, timeout=5000)
            else:
                return False
            await self._settle()
            self.log("success", f"Recovery succeeded for {action_type} on '{selector}'.")
            return True
        except Exception as rec_error:
            first_line = str(rec_error).strip().splitlines()[0] if str(rec_error).strip() else repr(rec_error)
            self.log("error", f"Recovery failed for '{selector}': {first_line}")
            return False

    async def capture_screenshot(self, name: str) -> str:
        return await self.runner.capture_screenshot(name)

    async def close(self):
        await self.runner.close_browser()


# Manual smoke test:  python -m backend.agents.tester
if __name__ == "__main__":

    async def run_test():
        tester = BrowserTester()
        await tester.start()
        await tester.navigate_to("https://example.com")
        await tester.capture_screenshot("step1_home_page")
        await tester.verify_assertion("text_visible", "Example Domain")
        await tester.execute_action("click", "a")
        await tester.capture_screenshot("step2_after_click")
        await tester.verify_assertion("url_contains", "iana.org")
        await tester.close()

    asyncio.run(run_test())
