"""
Content-consistency checks for the Document Authenticity validator.

Primary authenticity signal: verify that the values printed on an inspection
document actually match the values the platform already expects (from the task /
loan record). A document whose fields have been edited (amount, date, vehicle
number, reference id, inspector name, ...) will be missing the expected value.

Perception (reading the image) is delegated to app.utils.ocr_utils; the
comparison performed here is deterministic. This module returns a simple
dictionary. It does not build a ValidationResult or a RiskFlag, and does not
perform ELA, regex, checksum, amount-in-words or document-specific validation.
"""

from app.core.logger import get_logger
from app.models.request import ValidationRequest
from app.utils.ocr_utils import extract_text

logger = get_logger(__name__)


def extract_expected_values(
    request: ValidationRequest,
) -> dict:
    """
    Read the expected field values supplied by the caller.

    Convention (no request-model change required, requestJson is a free dict):
        requestJson = {"expectedFields": {"vehicleId": "MH12AB1234", ...}}

    Returns:
        dict of {field: expected_value}, empty when nothing usable was supplied.
    """

    request_json = request.requestJson or {}

    expected = request_json.get("expectedFields", {})

    if not isinstance(expected, dict):
        logger.warning("expectedFields is not an object; ignoring it.")
        return {}

    return {
        str(field): str(value)
        for field, value in expected.items()
        if value is not None and str(value).strip()
    }


def compare_expected_values(
    extracted_text: str,
    expected_fields: dict,
) -> dict:
    """
    Check that each expected value is present in the OCR-extracted text.

    Deterministic containment test after whitespace/case normalization.

    Returns:
        dict with matchedFields, failedFields and reasons.
    """

    strip_table = str.maketrans("", "", "-:/_")

    normalized_text = "".join(extracted_text.split()).translate(strip_table).upper()

    matched_fields = []
    failed_fields = []
    reasons = []

    for field, expected_value in expected_fields.items():

        normalized_value = (
            "".join(str(expected_value).split()).translate(strip_table).upper()
        )

        if normalized_value in normalized_text:
            matched_fields.append(field)
        else:
            failed_fields.append(field)
            reasons.append(
                f"Expected {field} '{expected_value}' "
                f"was not found in the document."
            )

    return {
        "matchedFields": matched_fields,
        "failedFields": failed_fields,
        "reasons": reasons,
    }


def check_content_consistency(
    request: ValidationRequest,
) -> dict:
    """
    Primary content-authenticity signal.

    Reuses ocr_utils.extract_text for perception, then deterministically checks
    the expected field values against the extracted text.

    Returns:
        {
            "matched": bool,          # absent when skipped
            "skipped": bool,          # True only when no expected fields supplied
            "fieldMatchRatio": float,
            "ocrConfidence": float,
            "matchedFields": [...],
            "failedFields": [...],
            "reasons": [...],
            "expectedFields": {...},
        }
    """

    logger.info("Content consistency check started")

    expected_fields = extract_expected_values(request)

    if not expected_fields:
        logger.info("No expected field values supplied for comparison.")
        return {
            "skipped": True,
            "fieldMatchRatio": 0.0,
            "ocrConfidence": 0.0,
            "matchedFields": [],
            "failedFields": [],
            "reasons": ["No expected field values were supplied for comparison."],
            "expectedFields": {},
        }

    extracted_text, ocr_confidence = extract_text(
        request.evidence.fileUrl
    )

    if not extracted_text.strip():
        logger.warning("No text extracted from the document.")
        return {
            "matched": False,
            "fieldMatchRatio": 0.0,
            "ocrConfidence": 0.0,
            "matchedFields": [],
            "failedFields": list(expected_fields.keys()),
            "reasons": ["No text could be extracted from the document."],
            "expectedFields": expected_fields,
        }

    comparison = compare_expected_values(
        extracted_text,
        expected_fields,
    )

    matched_fields = comparison["matchedFields"]
    failed_fields = comparison["failedFields"]
    reasons = comparison["reasons"]

    matched = len(failed_fields) == 0

    field_match_ratio = round(
        len(matched_fields) / len(expected_fields),
        2,
    )

    if matched:
        reasons = ["All expected values were found in the document."]

    logger.info(
        "Content consistency completed | matched=%s | %d/%d fields",
        matched,
        len(matched_fields),
        len(expected_fields),
    )

    return {
        "matched": matched,
        "fieldMatchRatio": field_match_ratio,
        "ocrConfidence": round(ocr_confidence, 2),
        "matchedFields": matched_fields,
        "failedFields": failed_fields,
        "reasons": reasons,
        "expectedFields": expected_fields,
    }
