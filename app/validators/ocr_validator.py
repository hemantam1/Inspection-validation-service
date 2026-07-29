from app.core.constants import OCR_MATCH_THRESHOLD
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


class OCRValidator(BaseValidator):

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidationResult:

        try:

            if request.evidence.evidenceType not in (
                EvidenceType.PHOTO,
                EvidenceType.DOCUMENT,
            ):
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

            if (
                expected_text is None
                or not expected_text.strip()
            ):
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

            extracted_text, ocr_confidence = extract_text(
                request.evidence.fileUrl
            )

            if not extracted_text:

                return ValidationResult(
                    confidenceScore=0,
                    result={
                        "expectedText": expected_text,
                        "extractedText": "",
                        "ocrConfidence": ocr_confidence,
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

            confidence = 95 if matched else 85

            risk_flags = []

            if not matched:

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

            return ValidationResult(
                confidenceScore=confidence,
                result={
                    "expectedText": expected_text,
                    "extractedText": extracted_text,
                    "ocrConfidence": ocr_confidence,
                    "matchScore": round(match_score, 2),
                    "textMatched": matched,
                },
                riskFlags=risk_flags,
                error=None,
            )

        except Exception as e:

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