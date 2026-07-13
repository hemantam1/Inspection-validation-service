from app.models.enums import RiskEventType, RiskSeverity
from app.models.request import ValidationRequest
from app.models.response import RiskFlag, ErrorInfo
from app.models.validation_result import ValidationResult
from app.utils.gps_utils import calculate_distance, within_radius
from app.validators.base_validator import BaseValidator

class GPSValidator(BaseValidator):
    """
    Validates whether the captured GPS location is within
    the allowed inspection radius.
    """

    def validate(self, request: ValidationRequest) -> ValidationResult:

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

        distance = calculate_distance(
            request.evidence.latitude,
            request.evidence.longitude,
            registered_location.latitude,
            registered_location.longitude,
        )

        within_allowed_radius = within_radius(
            distance,
            registered_location.radiusMeters,
        )

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
                        f"{registered_location.radiusMeters:.2f}m."
                    ),
                )
            )

        return ValidationResult(
            confidenceScore=95,
            result={
                "withinRadius": within_allowed_radius,
                "distanceMeters": round(distance, 2),
                "spoofingSuspected": not within_allowed_radius,
            },
            riskFlags=risk_flags,
            error=None,
        )