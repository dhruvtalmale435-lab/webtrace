import json
from pathlib import Path
from PIL import Image, ImageChops, ImageEnhance


def compare_screenshots(
    baseline_path,
    current_path,
    output_dir="backend/reports",
    pixel_threshold=20,
):
    if not isinstance(pixel_threshold, int) or isinstance(pixel_threshold, bool):
        raise TypeError("pixel_threshold must be an integer between 0 and 255")

    if not 0 <= pixel_threshold <= 255:
        raise ValueError("pixel_threshold must be between 0 and 255")

    baseline_path = Path(baseline_path)
    current_path = Path(current_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not baseline_path.is_file():
        raise FileNotFoundError(f"Baseline screenshot not found: {baseline_path}")

    if not current_path.is_file():
        raise FileNotFoundError(f"Current screenshot not found: {current_path}")

    with Image.open(baseline_path) as image:
        baseline = image.convert("RGB")

    with Image.open(current_path) as image:
        current = image.convert("RGB")

    baseline_size = baseline.size
    current_size = current.size
    size_mismatch = baseline_size != current_size

    if size_mismatch:
        comparison_size = (
            max(baseline.width, current.width),
            max(baseline.height, current.height),
        )

        baseline_canvas = Image.new("RGB", comparison_size, "black")
        current_canvas = Image.new("RGB", comparison_size, "black")

        baseline_canvas.paste(baseline, (0, 0))
        current_canvas.paste(current, (0, 0))

        baseline = baseline_canvas
        current = current_canvas

    difference = ImageChops.difference(baseline, current)
    grayscale = difference.convert("L")

    thresholded = grayscale.point(
        lambda value: 255 if value > pixel_threshold else 0
    )

    histogram = thresholded.histogram()
    changed_pixels = histogram[255]
    total_pixels = baseline.width * baseline.height
    difference_percentage = changed_pixels / total_pixels * 100

    diff_path = output_dir / "visual_diff.png"
    report_path = output_dir / "visual_regression_report.json"

    enhanced_difference = ImageEnhance.Contrast(difference).enhance(3)
    enhanced_difference.save(diff_path)

    report = {
        "baseline_path": str(baseline_path),
        "current_path": str(current_path),
        "baseline_dimensions": list(baseline_size),
        "current_dimensions": list(current_size),
        "dimensions_mismatch": size_mismatch,
        "pixel_threshold": pixel_threshold,
        "changed_pixels": changed_pixels,
        "total_pixels": total_pixels,
        "difference_percentage": round(difference_percentage, 2),
        "visual_changes_detected": changed_pixels > 0 or size_mismatch,
        "diff_image_path": str(diff_path),
    }

    report_path.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8",
    )

    return report


if __name__ == "__main__":
    print("Visual Regression module is ready.")
    print("Use compare_screenshots(baseline_path, current_path) to compare images.")
