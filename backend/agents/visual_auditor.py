import asyncio
from collections import Counter
from datetime import datetime
from pathlib import Path

from backend.agents.screenshot_highlighter import highlight_screenshot
from backend.visual_regression import compare_screenshots

# ---------------------------------------------------------------------------
# Shared JavaScript helpers (injected into every page.evaluate call)
# ---------------------------------------------------------------------------
JS_HELPERS = r"""
const cssPath = (el) => {
    if (!(el instanceof Element)) return '';
    if (el.id) return el.tagName.toLowerCase() + '#' + el.id;
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && node !== document.documentElement && parts.length < 4) {
        let part = node.tagName.toLowerCase();
        const parent = node.parentElement;
        if (parent) {
            const same = Array.from(parent.children).filter(c => c.tagName === node.tagName);
            if (same.length > 1) part += ':nth-of-type(' + (same.indexOf(node) + 1) + ')';
        }
        parts.unshift(part);
        node = parent;
    }
    return parts.join(' > ');
};

const rectOf = (el) => {
    const r = el.getBoundingClientRect();
    return {
        x: r.x + window.scrollX,
        y: r.y + window.scrollY,
        width: r.width,
        height: r.height
    };
};

const isVisible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 &&
        s.display !== 'none' &&
        s.visibility !== 'hidden' &&
        Number(s.opacity) > 0;
};

const accName = (el) => {
    const aria = (el.getAttribute('aria-label') || '').trim();
    if (aria) return aria;

    const labelledBy = el.getAttribute('aria-labelledby');
    if (labelledBy) {
        const t = labelledBy.split(/\s+/).map(id => {
            const n = document.getElementById(id);
            return n ? n.textContent.trim() : '';
        }).join(' ').trim();
        if (t) return t;
    }

    if (el.labels && el.labels.length) {
        const t = Array.from(el.labels).map(l => l.textContent.trim()).join(' ').trim();
        if (t) return t;
    }

    const textual = ['BUTTON', 'A', 'SUMMARY'].includes(el.tagName) ||
        el.getAttribute('role') === 'button';
    if (textual) {
        const t = (el.innerText || el.textContent || '').trim();
        if (t) return t;
    }

    if (el.tagName === 'INPUT' && ['button', 'submit', 'reset'].includes(el.type)) {
        const v = (el.value || '').trim();
        if (v) return v;
    }

    const innerImg = el.querySelector && el.querySelector('img[alt]');
    if (innerImg && innerImg.alt.trim()) return innerImg.alt.trim();

    const svgTitle = el.querySelector && el.querySelector('svg title');
    if (svgTitle && svgTitle.textContent.trim()) return svgTitle.textContent.trim();

    return (el.getAttribute('title') || '').trim();
};
"""


def _js(body):
    return "() => {\n" + JS_HELPERS + "\n" + body + "\n}"


SNAPSHOT_SCRIPT = _js(r"""
const selector = 'a, button, input:not([type="hidden"]), img, h1, h2, h3, [role="button"]';
const items = Array.from(document.querySelectorAll(selector)).slice(0, 300).map(el => {
    const tag = el.tagName.toLowerCase();
    const text = (el.innerText || el.value || el.alt || '').trim().slice(0, 40);
    const key = tag + '|' + (
        el.id || text || el.getAttribute('src') ||
        el.getAttribute('name') || cssPath(el)
    );
    return {
        key,
        tag,
        text,
        visible: isVisible(el),
        rect: rectOf(el)
    };
});

return {
    text: document.body.innerText.slice(0, 5000),
    images: Array.from(document.images).map(img => img.currentSrc || img.src),
    items
};
""")


CLS_SCRIPT = r"""
() => new Promise(resolve => {
    try {
        let total = 0;
        const observer = new PerformanceObserver(list => {
            for (const entry of list.getEntries()) {
                if (!entry.hadRecentInput) total += entry.value;
            }
        });
        observer.observe({ type: 'layout-shift', buffered: true });
        setTimeout(() => {
            observer.disconnect();
            resolve(total);
        }, 1000);
    } catch (e) {
        resolve(null);
    }
})
"""


class VisualAuditor:
    """
    Detects UI problems on a live Playwright page.

    Checks: HTTP errors, JavaScript errors, missing/hidden expected elements,
    broken images, images without alt, empty buttons, empty links, unlabeled
    form fields/checkboxes, horizontal overflow, element overlap, layout shift
    (CLS + element movement), dynamic content changes, disappearing elements
    (including after a reload), and optionally broken links.
    """

    MAX_BANNERS = 6

    def __init__(
        self,
        screenshot_dir=None,
        timeout=10000,
        observe_ms=1000,
        reload_check=True,
        max_links_to_check=25,
    ):
        self.screenshot_dir = Path(screenshot_dir or "backend/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        self.timeout = timeout
        self.observe_ms = observe_ms
        self.reload_check = reload_check
        self.max_links_to_check = max_links_to_check

        self.issues = []
        self.js_errors = []
        self.highlight_boxes = []
        self._issue_counter = 0
        self._seen = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _add_issue(
        self,
        category,
        description,
        severity="medium",
        element=None,
        evidence=None,
        confidence="high",
    ):
        """Add an issue. The same category + element is only reported once."""
        key = (category, str(element) if element is not None else description)

        if key in self._seen:
            return self._seen[key]

        self._issue_counter += 1

        issue = {
            "id": self._issue_counter,
            "category": category,
            "description": description,
            "severity": severity,
            "element": element,
            "evidence": evidence,
            "confidence": confidence,
        }

        self.issues.append(issue)
        self._seen[key] = issue
        return issue

    def _highlight(self, issue, rect, label):
        """Draw a box around an element on the annotated screenshot."""
        if not rect or rect.get("width", 0) <= 0 or rect.get("height", 0) <= 0:
            return

        self.highlight_boxes.append({
            "x": rect["x"],
            "y": rect["y"],
            "width": rect["width"],
            "height": rect["height"],
            "label": label,
            "category": issue["category"],
            "severity": issue["severity"],
            "id": issue["id"],
        })

    def _banner(self, issue, label):
        """Show a page-level issue as a banner above the screenshot."""
        self.highlight_boxes.append({
            "banner": True,
            "label": label,
            "category": issue["category"],
            "severity": issue["severity"],
            "id": issue["id"],
        })

    async def _safe_evaluate(self, page, script, default=None):
        try:
            return await page.evaluate(script)
        except Exception:
            return default

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------
    async def _check_missing_elements(self, page, expected_selectors):
        for selector in expected_selectors or []:
            try:
                locator = page.locator(selector)
                count = await locator.count()

                if count == 0:
                    issue = self._add_issue(
                        "missing_element",
                        f"Expected element was not found: {selector}",
                        severity="high",
                        element=selector,
                        evidence={"selector": selector},
                    )
                    self._banner(issue, f"Missing element: {selector}")
                    continue

                visible = False

                for index in range(count):
                    if await locator.nth(index).is_visible():
                        visible = True
                        break

                if not visible:
                    issue = self._add_issue(
                        "hidden_element",
                        f"Expected element exists but is not visible: {selector}",
                        severity="medium",
                        element=selector,
                        evidence={"selector": selector},
                    )
                    box = await locator.first.bounding_box()
                    if box:
                        scroll = await self._safe_evaluate(
                            page,
                            "() => ({x: window.scrollX, y: window.scrollY})",
                            {"x": 0, "y": 0},
                        )
                        self._highlight(
                            issue,
                            {
                                "x": box["x"] + scroll["x"],
                                "y": box["y"] + scroll["y"],
                                "width": box["width"],
                                "height": box["height"],
                            },
                            f"Hidden: {selector}",
                        )
                    else:
                        self._banner(issue, f"Hidden element: {selector}")

            except Exception as error:
                self._add_issue(
                    "selector_check_error",
                    f"Could not check selector {selector}: {error}",
                    severity="low",
                    element=selector,
                )

    async def _check_broken_images(self, page):
        images = await self._safe_evaluate(
            page,
            _js(r"""
            return Array.from(document.images).map(img => ({
                src: img.currentSrc || img.src || '',
                alt: img.getAttribute('alt'),
                complete: img.complete,
                lazy: img.loading === 'lazy',
                naturalWidth: img.naturalWidth,
                visible: isVisible(img),
                path: cssPath(img),
                rect: rectOf(img)
            }));
            """),
            [],
        )

        for image in images:
            src = image["src"]

            # Broken image: finished loading but has no pixels.
            if src and image["complete"] and image["naturalWidth"] == 0:
                rect = image["rect"]
                tiny = rect["width"] <= 32 and rect["height"] <= 32

                issue = self._add_issue(
                    "broken_image",
                    f"Image failed to load: {src}",
                    severity="low" if tiny else "medium",
                    element=image["path"],
                    evidence={
                        "src": src,
                        "alt": image["alt"] or "",
                        "selector": image["path"],
                    },
                )
                self._highlight(issue, rect, f"Broken image #{issue['id']}")
                continue

            # Working image with no alt attribute at all.
            if src and image["visible"] and image["alt"] is None:
                issue = self._add_issue(
                    "image_missing_alt",
                    f"Image has no alt attribute: {src}",
                    severity="low",
                    element=image["path"],
                    evidence={"src": src, "selector": image["path"]},
                    confidence="medium",
                )
                self._highlight(issue, image["rect"], f"No alt #{issue['id']}")

    async def _check_empty_buttons(self, page):
        buttons = await self._safe_evaluate(
            page,
            _js(r"""
            return Array.from(document.querySelectorAll(
                'button, input[type="button"], input[type="submit"], [role="button"]'
            )).map(el => ({
                name: accName(el),
                visible: isVisible(el),
                path: cssPath(el),
                rect: rectOf(el),
                html: el.outerHTML.slice(0, 200)
            }));
            """),
            [],
        )

        for button in buttons:
            if button["visible"] and not button["name"]:
                issue = self._add_issue(
                    "empty_button",
                    "Visible button has no detectable accessible name.",
                    severity="medium",
                    element=button["path"],
                    evidence={"html": button["html"], "selector": button["path"]},
                )
                self._highlight(
                    issue, button["rect"], f"Unnamed button #{issue['id']}"
                )

    async def _check_empty_links(self, page):
        links = await self._safe_evaluate(
            page,
            _js(r"""
            return Array.from(document.querySelectorAll('a[href]')).map(el => ({
                name: accName(el),
                visible: isVisible(el),
                href: el.getAttribute('href'),
                path: cssPath(el),
                rect: rectOf(el)
            }));
            """),
            [],
        )

        for link in links:
            if link["visible"] and not link["name"]:
                issue = self._add_issue(
                    "empty_link",
                    f"Visible link has no text or accessible name: {link['href']}",
                    severity="low",
                    element=link["path"],
                    evidence={"href": link["href"], "selector": link["path"]},
                    confidence="medium",
                )
                self._highlight(issue, link["rect"], f"Empty link #{issue['id']}")

    async def _check_horizontal_overflow(self, page):
        result = await self._safe_evaluate(
            page,
            _js(r"""
            const viewportWidth = document.documentElement.clientWidth;
            const documentWidth = document.documentElement.scrollWidth;
            const offenders = [];

            if (documentWidth > viewportWidth + 5) {
                const all = document.body ? document.body.querySelectorAll('*') : [];
                for (const el of all) {
                    if (offenders.length >= 3) break;
                    if (!isVisible(el)) continue;
                    const r = el.getBoundingClientRect();
                    if (r.right > viewportWidth + 5) {
                        offenders.push({
                            selector: cssPath(el),
                            rect: rectOf(el)
                        });
                    }
                }
            }

            return { viewportWidth, documentWidth, offenders };
            """),
            {},
        )

        if not result:
            return

        if result.get("documentWidth", 0) > result.get("viewportWidth", 0) + 5:
            offenders = result.get("offenders", [])

            issue = self._add_issue(
                "horizontal_overflow",
                "Page content extends beyond the viewport horizontally.",
                severity="medium",
                element=offenders[0]["selector"] if offenders else None,
                evidence={
                    "viewportWidth": result["viewportWidth"],
                    "documentWidth": result["documentWidth"],
                    "offenders": [o["selector"] for o in offenders],
                },
                confidence="medium",
            )

            self._banner(
                issue,
                f"Horizontal overflow: page {result['documentWidth']}px "
                f"> viewport {result['viewportWidth']}px",
            )

            for offender in offenders:
                self._highlight(issue, offender["rect"], f"Overflow #{issue['id']}")

    async def _check_layout_overlap(self, page):
        overlaps = await self._safe_evaluate(
            page,
            _js(r"""
            const elements = Array.from(document.querySelectorAll(
                'h1, h2, h3, button, input:not([type="hidden"]), img, p, a'
            )).filter(el => {
                const r = el.getBoundingClientRect();
                return r.width > 5 && r.height > 5 && isVisible(el);
            }).slice(0, 400);

            const results = [];

            for (let i = 0; i < elements.length && results.length < 5; i++) {
                const a = elements[i];
                const ar = a.getBoundingClientRect();

                for (let j = i + 1; j < elements.length; j++) {
                    const b = elements[j];
                    if (a.contains(b) || b.contains(a)) continue;

                    const br = b.getBoundingClientRect();
                    const width = Math.min(ar.right, br.right) - Math.max(ar.left, br.left);
                    const height = Math.min(ar.bottom, br.bottom) - Math.max(ar.top, br.top);
                    if (width <= 0 || height <= 0) continue;

                    const smaller = Math.min(ar.width * ar.height, br.width * br.height);
                    if (smaller > 0 && (width * height) / smaller > 0.65) {
                        results.push({
                            first: a.tagName.toLowerCase(),
                            second: b.tagName.toLowerCase(),
                            firstPath: cssPath(a),
                            secondPath: cssPath(b),
                            rect: rectOf(b)
                        });
                        break;
                    }
                }
            }

            return results;
            """),
            [],
        )

        for overlap in overlaps:
            issue = self._add_issue(
                "possible_layout_overlap",
                "Visible elements overlap substantially; manual review is recommended.",
                severity="low",
                element=f"{overlap['firstPath']} / {overlap['secondPath']}",
                evidence={
                    "first": overlap["first"],
                    "second": overlap["second"],
                },
                confidence="low",
            )
            self._highlight(issue, overlap["rect"], f"Overlap #{issue['id']}")

    async def _check_form_fields(self, page):
        fields = await self._safe_evaluate(
            page,
            _js(r"""
            return Array.from(document.querySelectorAll(
                'input:not([type="hidden"]):not([type="checkbox"]):not([type="submit"]):not([type="button"]):not([type="reset"]):not([type="image"]), textarea, select'
            )).map(el => ({
                tag: el.tagName.toLowerCase(),
                type: el.type || '',
                id: el.id,
                path: cssPath(el),
                hasLabel: !!accName(el),
                hasPlaceholder: !!(el.getAttribute('placeholder') || '').trim(),
                visible: isVisible(el),
                rect: rectOf(el)
            }));
            """),
            [],
        )

        for field in fields:
            if field["visible"] and not field["hasLabel"]:
                rect = field.pop("rect")
                issue = self._add_issue(
                    "form_field_without_label",
                    "Visible form field has no detectable associated label or accessible name.",
                    severity="low",
                    element=field["path"],
                    evidence=field,
                    confidence="medium",
                )
                self._highlight(issue, rect, f"No label #{issue['id']}")

    async def _check_checkboxes(self, page):
        checkboxes = await self._safe_evaluate(
            page,
            _js(r"""
            return Array.from(document.querySelectorAll('input[type="checkbox"]')).map(el => ({
                id: el.id,
                path: cssPath(el),
                checked: el.checked,
                disabled: el.disabled,
                hasLabel: !!accName(el),
                visible: isVisible(el),
                rect: rectOf(el)
            }));
            """),
            [],
        )

        for checkbox in checkboxes:
            if checkbox["visible"] and not checkbox["hasLabel"]:
                rect = checkbox.pop("rect")
                issue = self._add_issue(
                    "checkbox_without_label",
                    "Visible checkbox has no detectable associated label.",
                    severity="low",
                    element=checkbox["path"],
                    evidence=checkbox,
                    confidence="medium",
                )
                self._highlight(issue, rect, f"Checkbox no label #{issue['id']}")

    async def _check_links(self, page):
        links = await self._safe_evaluate(
            page,
            _js(r"""
            const seen = new Set();
            const out = [];
            for (const a of document.querySelectorAll('a[href]')) {
                const href = a.href;
                if (!/^https?:/i.test(href) || seen.has(href)) continue;
                seen.add(href);
                out.push({ href, path: cssPath(a), rect: rectOf(a), visible: isVisible(a) });
            }
            return out;
            """),
            [],
        )

        for link in links[: self.max_links_to_check]:
            try:
                response = await page.request.head(link["href"], timeout=5000)

                if response.status in (403, 405, 501):
                    response = await page.request.get(link["href"], timeout=5000)

                if response.status >= 400:
                    issue = self._add_issue(
                        "broken_link",
                        f"Link returned HTTP {response.status}: {link['href']}",
                        severity="medium",
                        element=link["path"],
                        evidence={
                            "href": link["href"],
                            "status": response.status,
                        },
                    )
                    if link["visible"]:
                        self._highlight(
                            issue,
                            link["rect"],
                            f"Broken link {response.status} #{issue['id']}",
                        )
            except Exception:
                continue

    async def _measure_cls(self, page):
        return await self._safe_evaluate(page, CLS_SCRIPT, None)

    async def _check_dynamic_behavior(self, page):
        """
        Compares observations of the page over time:
        text/image changes, elements that disappear, elements that move
        (layout shift) and cumulative layout shift. Optionally reloads the
        page to catch elements that appear/disappear between loads.
        """
        before = await self._safe_evaluate(page, SNAPSHOT_SCRIPT, None)
        if not before:
            return

        cls_task = asyncio.create_task(self._measure_cls(page))
        await page.wait_for_timeout(self.observe_ms)
        after = await self._safe_evaluate(page, SNAPSHOT_SCRIPT, None)
        cls_value = await cls_task

        if not after:
            return

        # --- Text / image changes -------------------------------------
        text_changed = before["text"] != after["text"]
        images_changed = before["images"] != after["images"]

        if text_changed or images_changed:
            issue = self._add_issue(
                "dynamic_content_changed",
                "Page text or image sources changed between observations. "
                "This may be expected behavior.",
                severity="info",
                evidence={
                    "text_changed": text_changed,
                    "images_changed": images_changed,
                },
                confidence="medium",
            )
            self._banner(issue, "Dynamic content changed during observation (info)")

        # --- Disappeared / moved elements ------------------------------
        before_items = {i["key"]: i for i in before["items"]}
        after_items = {i["key"]: i for i in after["items"]}

        disappeared = [
            before_items[key]
            for key, item in before_items.items()
            if item["visible"]
            and (key not in after_items or not after_items[key]["visible"])
        ]

        for item in disappeared[:5]:
            issue = self._add_issue(
                "element_disappeared",
                f"Element disappeared during observation: {item['key']}",
                severity="medium",
                element=item["key"],
                evidence={"key": item["key"], "text": item["text"]},
                confidence="medium",
            )
            self._highlight(issue, item["rect"], f"Disappeared #{issue['id']}")

        moved = []
        for key, old in before_items.items():
            new = after_items.get(key)
            if not new or not old["visible"] or not new["visible"]:
                continue

            dx = abs(new["rect"]["x"] - old["rect"]["x"])
            dy = abs(new["rect"]["y"] - old["rect"]["y"])
            dw = abs(new["rect"]["width"] - old["rect"]["width"])
            dh = abs(new["rect"]["height"] - old["rect"]["height"])

            if max(dx, dy, dw, dh) > 10:
                moved.append((old, new, max(dx, dy, dw, dh)))

        for old, new, delta in moved[:5]:
            issue = self._add_issue(
                "layout_shift",
                f"Element moved or resized by {round(delta)}px without user interaction: {old['key']}",
                severity="low",
                element=old["key"],
                evidence={"before": old["rect"], "after": new["rect"]},
                confidence="medium",
            )
            self._highlight(issue, old["rect"], f"Shifted #{issue['id']}")

        if cls_value is not None and cls_value > 0.1:
            issue = self._add_issue(
                "cumulative_layout_shift",
                f"Cumulative Layout Shift is {cls_value:.3f} "
                "(above the 0.1 'good' threshold).",
                severity="medium" if cls_value > 0.25 else "low",
                evidence={"cls": round(cls_value, 4)},
                confidence="medium",
            )
            self._banner(issue, f"Layout shift score (CLS): {cls_value:.3f}")

        # --- Reload comparison -----------------------------------------
        if self.reload_check:
            await self._check_reload_stability(page, after_items)

    async def _check_reload_stability(self, page, baseline_items):
        try:
            await page.reload(wait_until="load", timeout=self.timeout)
            await page.wait_for_timeout(500)
        except Exception:
            return

        reloaded = await self._safe_evaluate(page, SNAPSHOT_SCRIPT, None)
        if not reloaded:
            return

        reloaded_items = {i["key"]: i for i in reloaded["items"]}

        baseline_visible = {k for k, v in baseline_items.items() if v["visible"]}
        reloaded_visible = {k for k, v in reloaded_items.items() if v["visible"]}

        for key in sorted(baseline_visible - reloaded_visible)[:5]:
            item = baseline_items[key]
            issue = self._add_issue(
                "element_disappeared_after_reload",
                f"Element present on first load is missing after reload: {key}",
                severity="medium",
                element=key,
                evidence={"key": key, "text": item["text"]},
                confidence="medium",
            )
            self._highlight(issue, item["rect"], f"Gone after reload #{issue['id']}")

        for key in sorted(reloaded_visible - baseline_visible)[:5]:
            item = reloaded_items[key]
            self._add_issue(
                "element_appeared_after_reload",
                f"Element not present on first load appeared after reload: {key}",
                severity="low",
                element=key,
                evidence={"key": key, "text": item["text"]},
                confidence="low",
            )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def audit_page(
    self,
    page,
    expected_selectors=None,
    js_errors=None,
    check_links=False,
    page_status=None,
    baseline_screenshot=None,
    ):
        self.issues = []
        self.highlight_boxes = []
        self.js_errors = list(js_errors or [])
        self._issue_counter = 0
        self._seen = {}

        def on_page_error(error):
            message = str(error)
            if message not in self.js_errors:
                self.js_errors.append(message)

        page.on("pageerror", on_page_error)

        try:
            # 1. Page-level HTTP error
            if page_status is not None and page_status >= 400:
                issue = self._add_issue(
                    "page_http_error",
                    f"Page returned HTTP status {page_status}.",
                    severity="high",
                    evidence={"status": page_status, "url": page.url},
                )
                self._banner(issue, f"HTTP ERROR: {page_status}")

            # 2. Static checks (positions match the screenshot taken below)
            await self._check_missing_elements(page, expected_selectors)
            await self._check_broken_images(page)
            await self._check_empty_buttons(page)
            await self._check_empty_links(page)
            await self._check_horizontal_overflow(page)
            await self._check_layout_overlap(page)
            await self._check_form_fields(page)
            await self._check_checkboxes(page)

            if check_links:
                await self._check_links(page)

            # 3. Screenshot BEFORE the dynamic phase (which may reload the page)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            original_path = self.screenshot_dir / f"audit_{timestamp}.png"
            annotated_path = self.screenshot_dir / f"audit_{timestamp}_annotated.png"

            try:
                await page.screenshot(path=str(original_path), full_page=True)
            except Exception:
                await page.screenshot(path=str(original_path), full_page=False)

            device_scale = await self._safe_evaluate(
                page, "() => window.devicePixelRatio || 1", 1
            )

          # 4. Dynamic behavior checks
            await self._check_dynamic_behavior(page)
            # 5. JavaScript errors (includes errors raised during reload)
            for error in self.js_errors:
                issue = self._add_issue(
                    "javascript_error",
                    f"JavaScript runtime error: {error}",
                    severity="high",
                    element=error[:120],
                    evidence={"message": error},
                )
                self._banner(issue, f"JS ERROR: {error[:100]}")

            # 6. Annotated screenshot
            highlight_screenshot(
                input_path=str(original_path),
                output_path=str(annotated_path),
                boxes=self.highlight_boxes,
                scale=device_scale or 1,
            )
            # 7. Visual regression comparison
            visual_regression = None

            if baseline_screenshot is not None:
                try:
                    visual_regression = compare_screenshots(
                        baseline_path=baseline_screenshot,
                        current_path=original_path,
                    )

                    if visual_regression["visual_changes_detected"]:
                        self.issues.append({
                            "category": "visual_regression",
                            "severity": "medium",
                            "description": (
                                "Visual differences detected: "
                                f'{visual_regression["difference_percentage"]}% '
                                "of pixels changed compared with the baseline."
                            ),
                            "baseline_screenshot": str(baseline_screenshot),
                            "current_screenshot": str(original_path),
                            "diff_image": visual_regression["diff_image_path"],
                        })

                except Exception as error:
                    visual_regression = {
                        "status": "failed",
                        "error": str(error),
                    }

            return {
                "agent": "Visual Auditor",
                "status": "completed",
                "page_url": page.url,
                "visual_regression": visual_regression,
                "issues_found": len(self.issues),
                "issues": self.issues,
                "summary": {
                    "by_severity": dict(
                        Counter(i["severity"] for i in self.issues)
                    ),
                    "by_category": dict(
                        Counter(i["category"] for i in self.issues)
                    ),
                },
                "javascript_errors": self.js_errors,
                "screenshot": str(original_path),
                "annotated_screenshot": str(annotated_path),
            }

        finally:
            page.remove_listener("pageerror", on_page_error)