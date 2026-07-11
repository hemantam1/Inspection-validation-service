from app.models.enums import JobStatus
from app.models.request import ValidationRequest
from app.models.response import ValidationResponse
from app.models.validation_result import ValidationResult


class ResponseBuilder:
    

    @staticmethod
    def build(
        request: ValidationRequest,
        result: ValidationResult,
        status: JobStatus = JobStatus.COMPLETED,
    ) -> ValidationResponse:

        return ValidationResponse(
            jobId=request.jobId,
            status=status,
            resultType=request.jobType,
            confidenceScore=result.confidenceScore,
            resultJson=result.result,
            riskFlags=result.riskFlags,
            error=result.error,
        )