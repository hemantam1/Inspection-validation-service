from app.core.constants import DUPLICATE_SIMILARITY_THRESHOLD
from app.models.enums import RiskEventType, RiskSeverity
from app.models.request import ValidationRequest
from app.models.response import ErrorInfo, RiskFlag
from app.models.validation_result import ValidationResult
from app.utils.hash_utils import (
    load_image,
    calculate_phash,
    calculate_similarity,
)
from app.validators.base_validator import BaseValidator


class DuplicateValidator(BaseValidator):
    """
    Detects duplicate images using perceptual hashing.
    """

    def validate(self, request: ValidationRequest) -> ValidationResult:

        try:
            current_image = load_image(
                request.evidence.fileUrl
            )

            current_hash = calculate_phash(current_image)

            matches = []

            for reference_url in request.context.referenceEvidenceUrls:

                reference_image = load_image(reference_url)

                reference_hash = calculate_phash(reference_image)

                similarity = calculate_similarity(
                    current_hash,
                    reference_hash,
                )

                if similarity >= DUPLICATE_SIMILARITY_THRESHOLD:

                    matches.append(
                        {
                            "referenceUrl": reference_url,
                            "similarityScore": similarity,
                            "method": "perceptual_hash",
                        }
                    )

            is_duplicate = len(matches) > 0

            risk_flags = []

            if is_duplicate:

                best_match = max(
                    matches,
                    key=lambda x: x["similarityScore"],
                )

                risk_flags.append(
                    RiskFlag(
                        riskEventType=RiskEventType.DUPLICATE_IMAGE,
                        severity=RiskSeverity.CRITICAL,
                        score=50,
                        reason=(
                            f"{best_match['similarityScore'] * 100:.0f}% perceptual similarity "
                            f"to {best_match['referenceUrl']}"
                        ),
                    )
                )

            confidence = 95 if is_duplicate else 90

            return ValidationResult(
                confidenceScore=confidence,
                result={
                    "isDuplicate": is_duplicate,
                    "matches": matches,
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
                    code="DUPLICATE_VALIDATION_ERROR",
                    message="Failed to perform duplicate validation.",
                    details=str(e),
                ),
            )