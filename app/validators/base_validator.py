from abc import ABC, abstractmethod

from app.models.request import ValidationRequest
from app.models.validation_result import ValidationResult


class BaseValidator(ABC):

    @abstractmethod
    def validate(self, request: ValidationRequest) -> ValidationResult:
        pass