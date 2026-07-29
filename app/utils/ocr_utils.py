from functools import lru_cache
from pathlib import Path
import re

import easyocr
from rapidfuzz import fuzz


@lru_cache(maxsize=1)
def get_reader():
    """
    Initialize EasyOCR reader once and reuse it.
    """

    print("1. Creating EasyOCR Reader...")

    reader = easyocr.Reader(["en"], gpu=False)

    print("2. EasyOCR Reader Created.")

    return reader


def extract_text(image_path: str) -> tuple[str, int]:
    """
    Extract text from an image.

    Returns:
        tuple:
            extracted_text (str)
            average_confidence (0-100)
    """

    import cv2

    print("3. extract_text() called")

    image_path = Path(image_path).resolve()

    print(f"4. Resolved Image Path: {image_path}")

    if not image_path.exists():
        raise FileNotFoundError(image_path)

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(f"Unable to load image: {image_path}")

    print(f"5. Image Shape: {image.shape}")

    reader = get_reader()

    print("6. Calling readtext on numpy image...")

    results = reader.readtext(
        image,
        detail=1,
        paragraph=False,
    )

    print("7. OCR Finished")

    print(results)

    if not results:
        return "", 0

    extracted = []
    confidences = []

    for _, text, confidence in results:
        extracted.append(text)
        confidences.append(confidence)

    average_confidence = int(
        sum(confidences) / len(confidences) * 100
    )

    return " ".join(extracted), average_confidence


def normalize_text(text: str) -> str:
    """
    Normalize text before comparison.
    """

    text = text.upper().strip()

    text = re.sub(r"[^A-Z0-9]", "", text)

    return text


def calculate_match_score(
    expected: str,
    extracted: str,
) -> float:
    """
    Calculate similarity between expected
    and extracted text.

    Returns:
        float between 0 and 1
    """

    expected = normalize_text(expected)
    extracted = normalize_text(extracted)

    score = fuzz.ratio(expected, extracted) / 100.0

    print(f"11. Match Score: {score:.4f}")

    return score


def is_text_match(
    score: float,
    threshold: float,
) -> bool:
    """
    Determine whether OCR text matches expected text.
    """

    matched = score >= threshold

    print(f"12. Text Matched: {matched}")

    return matched