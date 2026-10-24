from PIL import Image
from backend.visual_regression import compare_screenshots

baseline_path = "backend/screenshots/regression_baseline.png"
current_path = "backend/screenshots/regression_different_size.png"

Image.new("RGB", (500, 350), "white").save(current_path)

report = compare_screenshots(
    baseline_path,
    current_path,
)

print("Baseline dimensions:", report["baseline_dimensions"])
print("Current dimensions:", report["current_dimensions"])
print("Dimension mismatch:", report["dimensions_mismatch"])
print("Difference percentage:", report["difference_percentage"], "%")
print("Visual changes detected:", report["visual_changes_detected"])

assert report["dimensions_mismatch"] is True
assert report["visual_changes_detected"] is True

print("PASS: Different screenshot dimensions detected.")