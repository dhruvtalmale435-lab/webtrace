from pathlib import Path

from PIL import Image, ImageDraw

from backend.agents.screenshot_highlighter import highlight_screenshot


def main():
    screenshot_dir = Path("backend/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    original_path = screenshot_dir / "highlighter_test_original.png"
    annotated_path = screenshot_dir / "highlighter_test_annotated.png"

    image = Image.new("RGB", (800, 500), "white")
    draw = ImageDraw.Draw(image)

    draw.rectangle(
        [100, 100, 350, 250],
        outline="black",
        width=2,
    )

    draw.text(
        (120, 120),
        "Example UI element",
        fill="black",
    )

    image.save(original_path)

    result = highlight_screenshot(
        input_path=str(original_path),
        output_path=str(annotated_path),
        boxes=[
            {
                "x": 100,
                "y": 100,
                "width": 250,
                "height": 150,
                "label": "BROKEN IMAGE",
                "severity": "medium",
            }
        ],
    )

    assert Path(result).is_file()

    with Image.open(result) as annotated:
        assert annotated.size == (800, 500)

    print("PASS: Original screenshot created")
    print("PASS: Annotated screenshot created")
    print("PASS: Image dimensions preserved")
    print(f"Annotated screenshot: {result}")


if __name__ == "__main__":
    main()
