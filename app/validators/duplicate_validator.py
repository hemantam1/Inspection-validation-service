from app.models.request import ValidationRequest
from app.models.validation_result import ValidationResult
from app.validators.base_validator import BaseValidator


class DuplicateValidator(BaseValidator):

    def validate(self, request: ValidationRequest) -> ValidationResult:
        return ValidationResult(
            confidenceScore=100,
            result={
                "isDuplicate": False,
                "matches": []
            },
            riskFlags=[],
            error=None
        )