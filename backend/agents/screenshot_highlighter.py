import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# One color + one readable name per issue category
# ---------------------------------------------------------------------------
CATEGORY_STYLE = {
    "missing_element": ((220, 38, 38), "Missing element"),
    "hidden_element": ((79, 70, 229), "Hidden element"),
    "broken_image": ((234, 88, 12), "Broken image"),
    "empty_button": ((147, 51, 234), "Empty button"),
    "horizontal_overflow": ((219, 39, 119), "Horizontal overflow"),
    "javascript_error": ((185, 28, 28), "JavaScript error"),
    "page_http_error": ((185, 28, 28), "HTTP error"),
    "broken_link": ((194, 65, 12), "Broken link"),
    "element_disappeared": ((190, 18, 60), "Element disappeared"),
    "element_disappeared_after_reload": ((190, 18, 60), "Gone after reload"),
    "image_missing_alt": ((13, 148, 136), "Image missing alt"),
    "form_field_without_label": ((2, 132, 199), "Field without label"),
    "checkbox_without_label": ((2, 132, 199), "Checkbox without label"),
    "empty_link": ((101, 140, 13), "Empty link"),
    "possible_layout_overlap": ((217, 119, 6), "Possible overlap"),
    "layout_shift": ((100, 116, 139), "Layout shift"),
    "cumulative_layout_shift": ((100, 116, 139), "Layout shift score"),
    "dynamic_content_changed": ((100, 116, 139), "Dynamic content"),
    "element_appeared_after_reload": ((100, 116, 139), "Appeared after reload"),
    "audit_may_be_blocked": ((120, 53, 15), "Audit may be blocked"),
}
DEFAULT_COLOR = (75, 85, 99)

BANNER_CATEGORIES = {"javascript_error", "page_http_error"}
MAX_RIBBONS = 4
MAX_LEGEND_ROWS = 14

PANEL_BG = (24, 28, 36)
PANEL_TEXT = (240, 242, 245)
PANEL_MUTED = (160, 168, 180)


def _color(category):
    return CATEGORY_STYLE.get(category, (DEFAULT_COLOR, None))[0]


def _name(category, fallback=None):
    named = CATEGORY_STYLE.get(category, (None, None))[1]
    if named:
        return named
    return fallback or str(category or "issue").replace("_", " ").capitalize()


def _font(size, bold=False):
    names = (
        ["arialbd.ttf", "Arial Bold.ttf", "segoeuib.ttf",
         "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"]
        if bold
        else ["arial.ttf", "Arial.ttf", "segoeui.ttf",
              "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    )

    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue

    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def _fit(draw, text, font, max_width):
    """Trim text with '...' so it fits in max_width pixels."""
    text = str(text)

    if max_width <= 0:
        return ""

    if draw.textlength(text, font=font) <= max_width:
        return text

    while text and draw.textlength(text + "...", font=font) > max_width:
        text = text[:-1]

    return text + "..."


def _intersects(a, b, pad=0):
    return not (
        a[2] + pad <= b[0]
        or b[2] + pad <= a[0]
        or a[3] + pad <= b[1]
        or b[3] + pad <= a[1]
    )


def _nearest(rect, point):
    """Closest point on a rectangle (l, t, r, b) to a point."""
    return (
        min(max(point[0], rect[0]), rect[2]),
        min(max(point[1], rect[1]), rect[3]),
    )


def _arrow(draw, start, end, color, width, head):
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    if length < 6:
        return

    draw.line([start, end], fill=color, width=width)

    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    left = (
        end[0] - head * math.cos(angle - math.pi / 6),
        end[1] - head * math.sin(angle - math.pi / 6),
    )
    right = (
        end[0] - head * math.cos(angle + math.pi / 6),
        end[1] - head * math.sin(angle + math.pi / 6),
    )
    draw.polygon([end, left, right], fill=color)


def _is_banner(box):
    return bool(box.get("banner")) or box.get("category") in BANNER_CATEGORIES


def _legend_height(row_count, columns, ui, has_more):
    if row_count == 0:
        return 0

    rows_per_column = math.ceil(row_count / columns)
    extra = 1 if has_more else 0

    return int(
        (52 + (rows_per_column + extra) * 32 + 14) * ui
    )


def highlight_screenshot(
    input_path,
    output_path,
    boxes=None,
    scale=1.0,
    legend=None,
    subtitle=None,
):
    """
    Annotate a screenshot so a person can see at a glance what is wrong.

    boxes   : list of dicts with x, y, width, height (CSS pixels, full-page
              coordinates), category, id and optional type ("bug"/"warning").
              Bugs get a numbered callout with an arrow, warnings get a small
              numbered badge. Dicts with banner=True (or JS/HTTP error
              categories) become red ribbons above the page.
    scale   : device pixel ratio of the screenshot (CSS px -> image px).
    legend  : list of dicts (id, type, category, severity, count, detail)
              drawn as a "Visual Auditor Findings" panel above the page.
    subtitle: optional line under the legend title (for example the URL).

    Nothing is drawn over the page header area, so page content is never
    hidden by banners or the legend.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Screenshot not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        scale = float(scale) if scale else 1.0
    except (TypeError, ValueError):
        scale = 1.0

    ui = max(1.0, min(scale, 2.5))

    with Image.open(input_path) as original:
        page_image = original.convert("RGB")

    boxes = list(boxes or [])
    legend = list(legend or [])

    ribbons = [b for b in boxes if _is_banner(b)][:MAX_RIBBONS]
    element_boxes = [b for b in boxes if not _is_banner(b)]

    ribbon_h = int(30 * ui)
    ribbons_total = len(ribbons) * ribbon_h

    shown_legend = legend[:MAX_LEGEND_ROWS]
    hidden_legend = len(legend) - len(shown_legend)
    columns = 2 if page_image.width >= 1000 and len(shown_legend) > 6 else 1
    legend_h = _legend_height(len(shown_legend), columns, ui, hidden_legend > 0)

    header_h = ribbons_total + legend_h

    canvas = Image.new(
        "RGB",
        (page_image.width, page_image.height + header_h),
        (255, 255, 255),
    )
    canvas.paste(page_image, (0, header_h))

    # -- translucent fills first (so outlines and labels stay crisp) --------
    placed = []
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    for box in element_boxes:
        try:
            x = float(box.get("x", 0)) * scale
            y = float(box.get("y", 0)) * scale
            width = float(box.get("width", 0)) * scale
            height = float(box.get("height", 0)) * scale
        except (TypeError, ValueError):
            continue

        if width <= 0 or height <= 0:
            continue

        left = int(max(0, min(x, page_image.width - 1)))
        top = int(max(0, min(y, page_image.height - 1)))
        right = int(max(left, min(x + width, page_image.width - 1)))
        bottom = int(max(top, min(y + height, page_image.height - 1)))

        if right - left < 1 and bottom - top < 1:
            continue

        top += header_h
        bottom += header_h

        is_warning = box.get("type") == "warning"
        color = _color(box.get("category"))

        overlay_draw.rectangle(
            [left, top, right, bottom],
            fill=color + (28 if is_warning else 46,),
        )
        placed.append((box, (left, top, right, bottom), color, is_warning))

    canvas = Image.alpha_composite(
        canvas.convert("RGBA"), overlay
    ).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    pill_font = _font(int(15 * ui), bold=True)
    badge_font = _font(int(13 * ui), bold=True)
    ribbon_font = _font(int(15 * ui), bold=True)
    title_font = _font(int(18 * ui), bold=True)
    row_font = _font(int(14 * ui), bold=True)
    muted_font = _font(int(13 * ui))

    # -- ribbons (JavaScript / HTTP errors, missing elements) ---------------
    for index, ribbon in enumerate(ribbons):
        color = _color(ribbon.get("category"))
        top = index * ribbon_h

        draw.rectangle(
            [0, top, canvas.width - 1, top + ribbon_h - 1],
            fill=(255, 235, 235),
            outline=color,
            width=2,
        )

        number = f"{ribbon['id']}. " if ribbon.get("id") else ""
        text = _fit(
            draw,
            number + str(ribbon.get("label") or _name(ribbon.get("category"))),
            ribbon_font,
            canvas.width - int(24 * ui),
        )
        draw.text(
            (int(12 * ui), top + int(6 * ui)),
            text,
            fill=color,
            font=ribbon_font,
        )

    # -- legend panel --------------------------------------------------------
    if legend_h:
        panel_top = ribbons_total
        draw.rectangle(
            [0, panel_top, canvas.width, panel_top + legend_h],
            fill=PANEL_BG,
        )

        bugs = sum(1 for item in legend if item.get("type") != "warning")
        warnings = len(legend) - bugs

        draw.text(
            (int(16 * ui), panel_top + int(10 * ui)),
            "Visual Auditor Findings",
            fill=PANEL_TEXT,
            font=title_font,
        )

        summary = f"{bugs} bug(s)  |  {warnings} warning group(s)"
        if subtitle:
            summary += f"  |  {subtitle}"

        draw.text(
            (int(16 * ui), panel_top + int(32 * ui)),
            _fit(draw, summary, muted_font, canvas.width - int(32 * ui)),
            fill=PANEL_MUTED,
            font=muted_font,
        )

        rows_per_column = math.ceil(len(shown_legend) / columns)
        column_width = (canvas.width - int(32 * ui)) // columns
        row_h = int(32 * ui)
        radius = int(11 * ui)

        for index, item in enumerate(shown_legend):
            column = index // rows_per_column
            row = index % rows_per_column

            x0 = int(16 * ui) + column * column_width
            y0 = panel_top + int(58 * ui) + row * row_h
            color = _color(item.get("category"))
            is_warning = item.get("type") == "warning"

            cx, cy = x0 + radius, y0 + radius
            draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=color,
            )

            number = str(item.get("id", ""))
            nb = draw.textbbox((0, 0), number, font=badge_font)
            draw.text(
                (cx - (nb[2] - nb[0]) / 2 - nb[0],
                 cy - (nb[3] - nb[1]) / 2 - nb[1]),
                number,
                fill=(255, 255, 255),
                font=badge_font,
            )

            name = _name(item.get("category"))
            count = item.get("count", 1)
            if count and count > 1:
                name += f" x{count}"

            tag = "WARN" if is_warning else "BUG"
            tag_w = int(draw.textlength(tag, font=muted_font)) + int(14 * ui)

            text_x = x0 + radius * 2 + int(10 * ui)
            name_w = int(draw.textlength(name, font=row_font))
            draw.text((text_x, y0 + int(3 * ui)), name, fill=PANEL_TEXT, font=row_font)

            detail_x = text_x + name_w + int(10 * ui)
            detail_room = x0 + column_width - tag_w - detail_x - int(14 * ui)
            detail = _fit(draw, item.get("detail") or "", muted_font, detail_room)
            draw.text(
                (detail_x, y0 + int(4 * ui)),
                detail,
                fill=PANEL_MUTED,
                font=muted_font,
            )

            tag_x = x0 + column_width - tag_w - int(10 * ui)
            draw.rounded_rectangle(
                [tag_x, y0 + int(2 * ui), tag_x + tag_w, y0 + int(24 * ui)],
                radius=int(5 * ui),
                outline=color if not is_warning else PANEL_MUTED,
                width=1,
            )
            draw.text(
                (tag_x + int(7 * ui), y0 + int(4 * ui)),
                tag,
                fill=color if not is_warning else PANEL_MUTED,
                font=muted_font,
            )

        if hidden_legend > 0:
            row_top = (
                panel_top + int(58 * ui) + rows_per_column * row_h
            )
            draw.text(
                (int(16 * ui), row_top + int(3 * ui)),
                f"+ {hidden_legend} more finding(s) in the JSON report",
                fill=PANEL_MUTED,
                font=muted_font,
            )

    # -- outlines, callouts and badges ----------------------------------------
    obstacles = []
    page_top = header_h
    page_rect = (0, page_top, canvas.width, canvas.height)

    # Draw warnings first so bug callouts always end up on top.
    ordered = sorted(placed, key=lambda item: 0 if item[3] else 1)

    for box, rect, color, is_warning in ordered:
        left, top, right, bottom = rect

        draw.rectangle(
            [left, top, right, bottom],
            outline=color,
            width=max(2, int((2 if is_warning else 3) * ui)),
        )

        number = str(box.get("id", "")) if box.get("id") else ""

        if is_warning:
            if not number:
                continue

            r = int(10 * ui)
            cx = min(max(left, r), canvas.width - r)
            cy = min(max(top, page_top + r), canvas.height - r)

            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
            nb = draw.textbbox((0, 0), number, font=badge_font)
            draw.text(
                (cx - (nb[2] - nb[0]) / 2 - nb[0],
                 cy - (nb[3] - nb[1]) / 2 - nb[1]),
                number,
                fill=(255, 255, 255),
                font=badge_font,
            )
            continue

        label = _name(box.get("category"), box.get("label"))
        text = f"{number}. {label}" if number else label
        text = _fit(draw, text, pill_font, canvas.width - int(40 * ui))

        tb = draw.textbbox((0, 0), text, font=pill_font)
        pad_x, pad_y = int(10 * ui), int(5 * ui)
        pw = (tb[2] - tb[0]) + pad_x * 2
        ph = (tb[3] - tb[1]) + pad_y * 2
        gap = int(14 * ui)

        candidates = [
            (left, top - ph - gap),
            (right - pw, top - ph - gap),
            (left, bottom + gap),
            (right - pw, bottom + gap),
            (right + gap, top),
            (left - pw - gap, top),
            (left + 4, top + 4),
        ]

        chosen = None

        for index, (px, py) in enumerate(candidates):
            px = int(min(max(px, 0), max(0, canvas.width - pw)))
            py = int(min(max(py, page_top), max(page_top, canvas.height - ph)))
            pill = (px, py, px + pw, py + ph)

            last = index == len(candidates) - 1

            if not last and _intersects(pill, rect):
                continue

            if not last and any(_intersects(pill, other, 4) for other in obstacles):
                continue

            chosen = pill
            break

        if chosen is None:
            chosen = (left, top, left + pw, top + ph)

        obstacles.append(chosen)
        px, py = chosen[0], chosen[1]

        # Arrow from the callout to the problem area.
        if not _intersects(chosen, rect):
            pill_center = ((chosen[0] + chosen[2]) / 2, (chosen[1] + chosen[3]) / 2)
            box_center = ((left + right) / 2, (top + bottom) / 2)

            start = _nearest(chosen, box_center)
            end = _nearest(rect, pill_center)
            _arrow(draw, start, end, color, max(2, int(2 * ui)), int(11 * ui))

        draw.rounded_rectangle(
            [px, py, px + pw, py + ph],
            radius=int(6 * ui),
            fill=color,
        )
        draw.text(
            (px + pad_x - tb[0], py + pad_y - tb[1]),
            text,
            fill=(255, 255, 255),
            font=pill_font,
        )

    canvas.save(output_path)
    return str(output_path)