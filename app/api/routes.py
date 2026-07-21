from fastapi import APIRouter, HTTPException

from app.models.request import ValidationRequest
from app.models.response import ValidationResponse
from app.services.validation_service import ValidationService

router = APIRouter()

validation_service = ValidationService()


@router.post(
    "/validate",
    response_model=ValidationResponse,
    summary="Execute AI validation",
)
def validate(
    request: ValidationRequest,
) -> ValidationResponse:

    return validation_service.validate(request)


@router.get(
    "/results",
    summary="Get all validation results",
)
def get_all_results():

    return validation_service.get_all_results()


@router.get(
    "/results/{job_id}",
    summary="Get validation result by Job ID",
)
def get_result(
    job_id: str,
):

    result = validation_service.get_result(job_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return result


@router.get(
    "/stats",
    summary="Get validation statistics",
)
def get_stats():

    return validation_service.get_stats()