import os

import pytesseract
from PIL import Image
from pytesseract import Output
from rapidfuzz import fuzz

from app.core.logger import get_logger

logger = get_logger(__name__)

_TESSERACT_CMD = os.getenv("TESSERACT_CMD")
if _TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = _TESSERACT_CMD

_TESSERACT_CONFIG = os.getenv("TESSERACT_CONFIG", "--oem 3 --psm 6")
_TESSERACT_LANG = os.getenv("TESSERACT_LANG", "eng")


def extract_text(image_path):

    logger.info("OCR extraction started | image=%s", image_path)

    try:
        with Image.open(image_path) as image:
            data = pytesseract.image_to_data(
                image,
                lang=_TESSERACT_LANG,
                config=_TESSERACT_CONFIG,
                output_type=Output.DICT,
            )
    except FileNotFoundError:
        logger.error("OCR image not found: %s", image_path)
        raise
    except Exception:
        logger.exception("Failed to open image: %s", image_path)
        raise

    try:
        data = pytesseract.image_to_data(
            image,
            lang=_TESSERACT_LANG,
            config=_TESSERACT_CONFIG,
            output_type=Output.DICT,
        )
    except pytesseract.TesseractNotFoundError:
        logger.exception(
            "Tesseract executable not found. "
            "Install Tesseract or configure TESSERACT_CMD."
        )
        raise
    except Exception:
        logger.exception("OCR execution failed for image: %s", image_path)
        raise

    words = []
    confidences = []

    # image_to_data returns parallel lists.
    # Confidence = -1 indicates non-text regions.
    for text, conf in zip(data.get("text", []), data.get("conf", [])):
        token = (text or "").strip()

        if not token:
            continue

        try:
            conf_value = float(conf)
        except (TypeError, ValueError):
            continue

        if conf_value < 0:
            continue

        words.append(token)
        confidences.append(conf_value)

    extracted_text = " ".join(words)

    average_confidence = (
        sum(confidences) / len(confidences)
        if confidences
        else 0.0
    )

    logger.info(
        "OCR extraction completed | words=%d | avg_confidence=%.2f",
        len(words),
        average_confidence,
    )

    logger.debug("Extracted OCR Text: %s", extracted_text)

    return extracted_text, average_confidence


def calculate_match_score(expected, extracted):
    """
    Calculate similarity score between expected and extracted text.

    Returns:
        float: RapidFuzz token_sort_ratio score (0-100).
    """

    score = fuzz.token_sort_ratio(
        expected.lower(),
        extracted.lower(),
    )

    logger.debug("OCR Match Score: %.2f", score)

    return score


def is_text_match(score, threshold):
    """
    Determine whether OCR output satisfies the configured similarity threshold.

    Args:
        score (float):
            Similarity score (0-100).

        threshold (float):
            Minimum score required for a successful match.

    Returns:
        bool
    """

    matched = score >= threshold

    logger.debug(
        "OCR Match Evaluation | score=%.2f | threshold=%s | matched=%s",
        score,
        threshold,
        matched,
    )

    return matched