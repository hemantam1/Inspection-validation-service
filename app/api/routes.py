from fastapi import APIRouter

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
def validate(request: ValidationRequest) -> ValidationResponse:

    return validation_service.validate(request)