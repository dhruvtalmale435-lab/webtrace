from pathlib import Path
from PIL import Image, ImageDraw
from backend.visual_regression import compare_screenshots


def main():
    screenshot_dir = Path("backend/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    baseline_path = screenshot_dir / "regression_baseline.png"
    identical_path = screenshot_dir / "regression_identical.png"
    modified_path = screenshot_dir / "regression_modified.png"
    different_size_path = screenshot_dir / "regression_different_size.png"

    baseline = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(baseline)
    draw.rectangle([50, 50, 150, 120], fill="blue")
    baseline.save(baseline_path)

    baseline.save(identical_path)

    modified = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(modified)
    draw.rectangle([50, 50, 150, 120], fill="red")
    modified.save(modified_path)

    Image.new("RGB", (500, 350), "white").save(different_size_path)

    identical_result = compare_screenshots(
        baseline_path,
        identical_path,
    )

    modified_result = compare_screenshots(
        baseline_path,
        modified_path,
    )

    custom_threshold_result = compare_screenshots(
        baseline_path,
        modified_path,
        pixel_threshold=50,
    )

    dimension_result = compare_screenshots(
        baseline_path,
        different_size_path,
    )

    assert identical_result["difference_percentage"] == 0.0
    assert identical_result["visual_changes_detected"] is False
    print("PASS: Identical screenshots show 0% difference.")

    assert modified_result["difference_percentage"] > 0
    assert modified_result["visual_changes_detected"] is True
    print(
        "PASS: Modified screenshots show a difference of "
        f"{modified_result['difference_percentage']}%."
    )

    assert custom_threshold_result["pixel_threshold"] == 50
    assert custom_threshold_result["difference_percentage"] > 0
    print("PASS: Custom pixel threshold is accepted.")

    assert dimension_result["dimensions_mismatch"] is True
    assert dimension_result["visual_changes_detected"] is True
    print("PASS: Different screenshot dimensions are detected.")

    try:
        compare_screenshots(
            baseline_path,
            modified_path,
            pixel_threshold=300,
        )
    except ValueError:
        print("PASS: Invalid pixel threshold is rejected.")
    else:
        raise AssertionError("Invalid pixel threshold was not rejected.")

    print(f"Difference image: {modified_result['diff_image_path']}")
    print("Report: backend/reports/visual_regression_report.json")
    print("All visual regression tests passed.")


if __name__ == "__main__":
    main()
