import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from app.core.constants import BLUR_THRESHOLD
from app.utils.image_utils import (
    load_image,
    calculate_blur_score,
    is_blurry,
)

BENCHMARK_FOLDER = Path(
    r"E:\inspection-validation-service\samples\images\blur_benchmark"
)

print("=" * 95)
print(f"{'Image':40} {'Expected':12} {'Predicted':12} {'Score':10} {'Status'}")
print("=" * 95)

total = 0
correct = 0

for image_path in sorted(BENCHMARK_FOLDER.glob("*.jpg")):

    filename = image_path.name.lower()

    if "sharp" in filename:
        expected = "SHARP"

    elif (
        "blur" in filename
        or "slight" in filename
        or "moderate" in filename
        or "heavy" in filename
    ):
        expected = "BLUR"

    else:
        continue

    image = load_image(str(image_path))

    blur_score = calculate_blur_score(image)

    blurry = is_blurry(
        blur_score,
        BLUR_THRESHOLD,
    )

    predicted = "BLUR" if blurry else "SHARP"

    status = (
        "PASS"
        if expected == predicted
        else "FAIL"
    )

    total += 1

    if status == "PASS":
        correct += 1

    print(
        f"{filename:40}"
        f"{expected:12}"
        f"{predicted:12}"
        f"{blur_score:10.2f}"
        f"{status}"
    )

print("=" * 95)

accuracy = (
    (correct / total) * 100
    if total > 0
    else 0
)

print(f"Total Images : {total}")
print(f"Correct      : {correct}")
print(f"Accuracy     : {accuracy:.2f}%")
print(f"Threshold    : {BLUR_THRESHOLD}")
print("=" * 95)