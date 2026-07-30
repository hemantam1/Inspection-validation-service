from app.core.constants import (
    OCR_MATCH_THRESHOLD,
    OCR_CONFIDENCE_PENALTY,
)
from app.core.logger import get_logger
from app.models.enums import (
    EvidenceType,
    RiskEventType,
    RiskSeverity,
)
from app.models.request import ValidationRequest
from app.models.response import (
    ErrorInfo,
    RiskFlag,
)
from app.models.validation_result import ValidationResult
from app.utils.ocr_utils import (
    calculate_match_score,
    extract_text,
    is_text_match,
)
from app.validators.base_validator import BaseValidator

logger = get_logger(__name__)


class OCRValidator(BaseValidator):

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidationResult:

        logger.info("OCR validation started")

        try:

            logger.debug(
                "Evidence type: %s",
                request.evidence.evidenceType,
            )

            if request.evidence.evidenceType not in (
                EvidenceType.PHOTO,
                EvidenceType.DOCUMENT,
            ):
                logger.warning(
                    "Unsupported evidence type: %s",
                    request.evidence.evidenceType,
                )

                return ValidationResult(
                    confidenceScore=0,
                    result={},
                    riskFlags=[],
                    error=ErrorInfo(
                        code="INVALID_EVIDENCE_TYPE",
                        message=(
                            "OCR validation supports "
                            "PHOTO and DOCUMENT evidence only."
                        ),
                    ),
                )

            expected_text = request.context.expectedText

            if expected_text is None or not expected_text.strip():
                logger.warning("Missing expectedText in validation context")

                return ValidationResult(
                    confidenceScore=0,
                    result={},
                    riskFlags=[],
                    error=ErrorInfo(
                        code="INVALID_CONTEXT",
                        message=(
                            "expectedText is required "
                            "for OCR validation."
                        ),
                    ),
                )

            logger.info(
                "Running OCR on image: %s",
                request.evidence.fileUrl,
            )

            extracted_text, ocr_confidence = extract_text(
                request.evidence.fileUrl
            )

            logger.info(
                "OCR completed | confidence=%.2f",
                ocr_confidence,
            )

            if not extracted_text.strip():

                logger.warning("No text extracted from image")

                return ValidationResult(
                    confidenceScore=0,
                    result={
                        "expectedText": expected_text,
                        "extractedText": "",
                        "ocrConfidence": 0.0,
                        "textMatched": False,
                        "matchScore": 0.0,
                    },
                    riskFlags=[
                        RiskFlag(
                            riskEventType=RiskEventType.DOCUMENT_FRAUD,
                            severity=RiskSeverity.MEDIUM,
                            score=20,
                            reason="Unable to detect text from the image.",
                        )
                    ],
                    error=ErrorInfo(
                        code="OCR_VALIDATION_ERROR",
                        message="No text could be extracted.",
                    ),
                )

            match_score = calculate_match_score(
                expected_text,
                extracted_text,
            )

            matched = is_text_match(
                match_score,
                OCR_MATCH_THRESHOLD,
            )

            logger.info(
                "OCR Match | score=%.2f | threshold=%s | matched=%s",
                match_score,
                OCR_MATCH_THRESHOLD,
                matched,
            )

            confidence = (
                round(ocr_confidence)
                if matched
                else max(round(ocr_confidence - OCR_CONFIDENCE_PENALTY), 0)
            )

            risk_flags = []

            if not matched:
                logger.warning(
                    "OCR text mismatch detected. "
                    "Adding DOCUMENT_FRAUD risk flag."
                )

                risk_flags.append(
                    RiskFlag(
                        riskEventType=RiskEventType.DOCUMENT_FRAUD,
                        severity=RiskSeverity.MEDIUM,
                        score=20,
                        reason=(
                            "OCR extracted text does not "
                            "match the expected text."
                        ),
                    )
                )

            logger.info("OCR validation completed successfully")

            return ValidationResult(
                confidenceScore=confidence,
                result={
                    "expectedText": expected_text,
                    "extractedText": extracted_text,
                    "ocrConfidence": round(ocr_confidence, 2),
                    "matchScore": round(match_score, 2),
                    "textMatched": matched,
                },
                riskFlags=risk_flags,
                error=None,
            )

        except Exception as e:

            logger.exception(
                "OCR validation failed: %s",
                str(e),
            )

            return ValidationResult(
                confidenceScore=0,
                result={},
                riskFlags=[],
                error=ErrorInfo(
                    code="OCR_VALIDATION_ERROR",
                    message="Failed to perform OCR validation.",
                    details=str(e),
                ),
            )