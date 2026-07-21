from app.builders.response_builder import ResponseBuilder
from app.factory.validator_factory import ValidatorFactory
from app.models.request import ValidationRequest
from app.models.response import ValidationResponse
from app.repositories.validation_repository import ValidationRepository


class ValidationService:

    def __init__(self):
        self.repository = ValidationRepository()

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidationResponse:

        validator = ValidatorFactory.get_validator(
            request.jobType
        )

        result = validator.validate(request)

        self.repository.save(
            request=request,
            result=result,
        )

        response = ResponseBuilder.build(
            request=request,
            result=result,
        )

        return response

    def get_all_results(self):
        return self.repository.get_all()

    def get_result(
        self,
        job_id: str,
    ):
        return self.repository.get_by_job_id(job_id)

    def get_stats(self):
        return self.repository.get_stats()