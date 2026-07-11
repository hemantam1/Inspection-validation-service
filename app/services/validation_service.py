from app.builders.response_builder import ResponseBuilder
from app.factory.validator_factory import ValidatorFactory
from app.models.request import ValidationRequest
from app.models.response import ValidationResponse


class ValidationService:

    def validate(self, request: ValidationRequest) -> ValidationResponse:

        validator = ValidatorFactory.get_validator(request.jobType)
        result = validator.validate(request)
        response = ResponseBuilder.build(
            request=request,
            result=result,
        )

        return response