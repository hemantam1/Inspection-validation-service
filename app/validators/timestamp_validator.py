from app.core.constants import MIN_CAPTURE_INTERVAL_SECONDS
from app.models.enums import RiskEventType, RiskSeverity
from app.models.request import ValidationRequest
from app.models.response import ErrorInfo, RiskFlag
from app.models.validation_result import ValidationResult
from app.utils.datetime_utils import (
    seconds_between,
    is_fast_submission,
)
from app.validators.base_validator import BaseValidator


class TimestampValidator(BaseValidator):

    def validate(self, request: ValidationRequest) -> ValidationResult:

        captured_at = request.evidence.capturedAt
        task_started_at = request.context.taskStartedAt
        prior_step_at = request.context.priorStepCapturedAt

        anomaly_detected = False
        reason = None

        risk_flags = []

        # Rule 1
        if task_started_at and captured_at < task_started_at:

            anomaly_detected = True
            reason = "Capture timestamp is earlier than task start."

        # Rule 2
        elif prior_step_at and captured_at < prior_step_at:

            anomaly_detected = True
            reason = "Capture timestamp is earlier than previous step."

        # Rule 3
        elif prior_step_at:

            interval = seconds_between(
                prior_step_at,
                captured_at,
            )

            if is_fast_submission(
                interval,
                MIN_CAPTURE_INTERVAL_SECONDS,
            ):

                anomaly_detected = True

                reason = (
                    f"Capture occurred only "
                    f"{interval:.1f} seconds after previous step."
                )

        if anomaly_detected:

            risk_flags.append(
                RiskFlag(
                    riskEventType=RiskEventType.TIMESTAMP_ANOMALY,
                    severity=RiskSeverity.HIGH,
                    score=35,
                    reason=reason,
                )
            )

        return ValidationResult(
            confidenceScore=95 if not anomaly_detected else 80,
            result={
                "anomalyDetected": anomaly_detected,
                "reason": reason,
            },
            riskFlags=risk_flags,
            error=None,
        )