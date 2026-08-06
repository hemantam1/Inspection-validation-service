from app.core.constants import (
    DOCUMENT_AUTHENTICITY_RISK_SCORE,
    ELA_THRESHOLD,
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
from app.utils.authenticity_utils import (
    calculate_authenticity_score,
    perform_ela,
)
from app.utils.content_consistency import (
    check_content_consistency,
)
from app.validators.base_validator import BaseValidator

logger = get_logger(__name__)


class DocumentAuthenticityValidator(BaseValidator):

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidationResult:

        logger.info(
            "Document Authenticity validation started"
        )

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
                            "Document Authenticity validation "
                            "supports PHOTO and DOCUMENT "
                            "evidence only."
                        ),
                    ),
                )

            logger.info(
                "Running ELA on image: %s",
                request.evidence.fileUrl,
            )

            localized_error, hotspot_contrast = perform_ela(
                request.evidence.fileUrl,
            )

            authenticity_score = calculate_authenticity_score(
                localized_error,
                hotspot_contrast,
            )

            tampering_detected = (
                localized_error >= ELA_THRESHOLD
            )

            logger.info(
                (
                    "ELA Result | "
                    "localized_error=%.2f | "
                    "hotspot_contrast=%.2f | "
                    "threshold=%.2f | "
                    "tampered=%s"
                ),
                localized_error,
                hotspot_contrast,
                ELA_THRESHOLD,
                tampering_detected,
            )

            content_result = check_content_consistency(request)

            content_skipped = content_result.get("skipped", False)
            content_matched = content_result.get("matched", True)
            content_mismatch = (
                not content_skipped and not content_matched
            )

            logger.info(
                (
                    "Content Consistency | "
                    "skipped=%s | "
                    "matched=%s"
                ),
                content_skipped,
                content_matched,
            )

            # A content mismatch overrides the ELA verdict: the document must be
            # treated as not authentic. When content is skipped or matched, the
            # existing ELA behaviour is preserved exactly.
            tampering_suspected = (
                tampering_detected or content_mismatch
            )
            is_authentic = not tampering_suspected

            risk_flags = []

            if tampering_detected:

                logger.warning(
                    "Possible document tampering detected."
                )

                risk_flags.append(
                    RiskFlag(
                        riskEventType=(
                            RiskEventType.DOCUMENT_FRAUD
                        ),
                        severity=RiskSeverity.MEDIUM,
                        score=DOCUMENT_AUTHENTICITY_RISK_SCORE,
                        reason=(
                            "Possible image tampering "
                            "detected using Error Level "
                            "Analysis."
                        ),
                    )
                )

            if content_mismatch:

                logger.warning(
                    "Document content does not match expected values."
                )

                risk_flags.append(
                    RiskFlag(
                        riskEventType=(
                            RiskEventType.DOCUMENT_FRAUD
                        ),
                        severity=RiskSeverity.MEDIUM,
                        score=DOCUMENT_AUTHENTICITY_RISK_SCORE,
                        reason=(
                            "Document content does not match "
                            "expected values: "
                            + "; ".join(
                                content_result.get("reasons", [])
                            )
                        ),
                    )
                )

            logger.info(
                "Document Authenticity validation completed."
            )

            return ValidationResult(
                confidenceScore=authenticity_score,
                result={
                    "isAuthentic": is_authentic,
                    "tamperingSuspected": tampering_suspected,
                    "authenticityScore": (
                        authenticity_score
                    ),
                    "localizedError": round(
                        localized_error,
                        2,
                    ),
                    "hotspotContrast": round(
                        hotspot_contrast,
                        2,
                    ),
                    "threshold": ELA_THRESHOLD,
                    "method": "Localized Error Level Analysis",
                    "contentConsistency": content_result,
                },
                riskFlags=risk_flags,
                error=None,
            )

        except Exception as e:

            logger.exception(
                (
                    "Document Authenticity "
                    "validation failed: %s"
                ),
                str(e),
            )

            return ValidationResult(
                confidenceScore=0,
                result={},
                riskFlags=[],
                error=ErrorInfo(
                    code="DOCUMENT_AUTHENTICITY_ERROR",
                    message=(
                        "Failed to perform document "
                        "authenticity validation."
                    ),
                    details=str(e),
                ),
            )
