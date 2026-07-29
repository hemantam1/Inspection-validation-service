from app.core.gps_config import AREA_RADIUS
from app.models.enums import RiskEventType, RiskSeverity
from app.models.request import ValidationRequest
from app.models.response import ErrorInfo, RiskFlag
from app.models.validation_result import ValidationResult
from app.utils.gps_utils import calculate_distance, within_radius
from app.validators.base_validator import BaseValidator


class GPSValidator(BaseValidator):
    """
    Validates whether the captured GPS location is within
    the allowed inspection radius.
    """

    def validate(self, request: ValidationRequest) -> ValidationResult:

        try:

            registered_location = request.context.registeredLocation

            if registered_location is None:
                return ValidationResult(
                    confidenceScore=0,
                    result={
                        "withinRadius": False,
                        "distanceMeters": None,
                        "spoofingSuspected": False,
                    },
                    riskFlags=[],
                    error=ErrorInfo(
                        code="REGISTERED_LOCATION_MISSING",
                        message="Registered location is required for GPS validation.",
                    ),
                )

            # Validate evidence GPS coordinates
            if (
                request.evidence.latitude is None
                or request.evidence.longitude is None
            ):
                return ValidationResult(
                    confidenceScore=0,
                    result={},
                    riskFlags=[],
                    error=ErrorInfo(
                        code="INVALID_GPS_COORDINATES",
                        message="Latitude and longitude are required for GPS validation.",
                    ),
                )

            if not (
                -90 <= request.evidence.latitude <= 90
                and -180 <= request.evidence.longitude <= 180
            ):
                return ValidationResult(
                    confidenceScore=0,
                    result={},
                    riskFlags=[],
                    error=ErrorInfo(
                        code="INVALID_GPS_COORDINATES",
                        message="Invalid GPS coordinates provided.",
                    ),
                )

            # Validate registered location coordinates
            if (
                registered_location.latitude is None
                or registered_location.longitude is None
            ):
                return ValidationResult(
                    confidenceScore=0,
                    result={},
                    riskFlags=[],
                    error=ErrorInfo(
                        code="INVALID_REGISTERED_LOCATION",
                        message="Registered location coordinates are invalid.",
                    ),
                )

            distance = calculate_distance(
                request.evidence.latitude,
                request.evidence.longitude,
                registered_location.latitude,
                registered_location.longitude,
            )

            allowed_radius = AREA_RADIUS[
                request.context.inspectionAreaType.value
            ]

            within_allowed_radius = within_radius(
                distance,
                allowed_radius,
            )

            gps_accuracy = request.evidence.gpsAccuracyM

            risk_flags = []

            if not within_allowed_radius:
                risk_flags.append(
                    RiskFlag(
                        riskEventType=RiskEventType.GPS_MISMATCH,
                        severity=RiskSeverity.HIGH,
                        score=40,
                        reason=(
                            f"Evidence captured {distance:.2f}m away from the "
                            f"registered location. Allowed radius: "
                            f"{allowed_radius:.2f}m."
                        ),
                    )
                )

            return ValidationResult(
                confidenceScore=95 if within_allowed_radius else 85,
                result={
                    "withinRadius": within_allowed_radius,
                    "distanceMeters": round(distance, 2),
                    "allowedRadius": allowed_radius,
                    "gpsAccuracyMeters": gps_accuracy,
                    "inspectionAreaType": request.context.inspectionAreaType.value,
                    "spoofingSuspected": not within_allowed_radius,
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
                    code="GPS_VALIDATION_ERROR",
                    message="Failed to perform GPS validation.",
                    details=str(e),
                ),
            )