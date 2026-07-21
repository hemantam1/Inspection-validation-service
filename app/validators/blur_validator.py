from app.core.constants import BLUR_THRESHOLD
from app.models.enums import RiskEventType, RiskSeverity
from app.models.request import ValidationRequest
from app.models.response import ErrorInfo, RiskFlag
from app.models.validation_result import ValidationResult
from app.utils.image_utils import (
    calculate_blur_score,
    is_blurry,
)
from app.utils.image_preprocessing import (
    preprocess_image,
)
from app.validators.base_validator import BaseValidator


class BlurValidator(BaseValidator):

    def validate(self, request: ValidationRequest) -> ValidationResult:
        try:

            image = preprocess_image(
                request.evidence.fileUrl
            )

            blur_score = calculate_blur_score(image)

            blurry = is_blurry(
                blur_score=blur_score,
                threshold=BLUR_THRESHOLD,
            )

            confidence = 95 if not blurry else 85

            risk_flags = []

            if blurry:
                risk_flags.append(
                    RiskFlag(
                        riskEventType=RiskEventType.BLUR_IMAGE,
                        severity=RiskSeverity.MEDIUM,
                        score=20,
                        reason=f"Blur score ({blur_score:.2f}) is below threshold ({BLUR_THRESHOLD}).",
                    )
                )

            return ValidationResult(
                confidenceScore=confidence,
                result={
                    "isBlurry": blurry,
                    "blurScore": round(blur_score, 2),
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
                    code="BLUR_VALIDATION_ERROR",
                    message="Failed to perform blur validation.",
                    details=str(e),
                ),
            )