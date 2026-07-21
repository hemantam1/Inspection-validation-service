from sqlalchemy import func

from app.database.connection import SessionLocal
from app.database.models import ValidationRecord
from app.models.enums import JobStatus
from app.models.request import ValidationRequest
from app.models.validation_result import ValidationResult


class ValidationRepository:

    def save(
        self,
        request: ValidationRequest,
        result: ValidationResult,
    ) -> None:

        db = SessionLocal()

        try:

            record = ValidationRecord(
                job_id=request.jobId,
                job_type=request.jobType.value,
                status=(
                    JobStatus.COMPLETED.value
                    if result.error is None
                    else JobStatus.FAILED.value
                ),
                confidence_score=result.confidenceScore,
                result_json=result.result,
                risk_flags=[
                    flag.model_dump()
                    for flag in result.riskFlags
                ],
                error=(
                    result.error.model_dump()
                    if result.error
                    else None
                ),
            )

            db.add(record)
            db.commit()

        finally:
            db.close()

    def get_all(self):

        db = SessionLocal()

        try:
            return db.query(ValidationRecord).all()

        finally:
            db.close()

    def get_by_job_id(
        self,
        job_id: str,
    ):

        db = SessionLocal()

        try:
            return (
                db.query(ValidationRecord)
                .filter(
                    ValidationRecord.job_id == job_id
                )
                .first()
            )

        finally:
            db.close()

    def get_stats(self):

        db = SessionLocal()

        try:

            return {
                "totalValidations": db.query(ValidationRecord).count(),

                "completed": db.query(ValidationRecord)
                .filter(
                    ValidationRecord.status == JobStatus.COMPLETED.value
                )
                .count(),

                "failed": db.query(ValidationRecord)
                .filter(
                    ValidationRecord.status == JobStatus.FAILED.value
                )
                .count(),

                "blurChecks": db.query(ValidationRecord)
                .filter(
                    ValidationRecord.job_type == "BLUR_CHECK"
                )
                .count(),

                "gpsChecks": db.query(ValidationRecord)
                .filter(
                    ValidationRecord.job_type == "GPS_CHECK"
                )
                .count(),

                "duplicateChecks": db.query(ValidationRecord)
                .filter(
                    ValidationRecord.job_type == "DUPLICATE_CHECK"
                )
                .count(),

                "timestampChecks": db.query(ValidationRecord)
                .filter(
                    ValidationRecord.job_type == "TIMESTAMP_ANOMALY_CHECK"
                )
                .count(),
            }

        finally:
            db.close()