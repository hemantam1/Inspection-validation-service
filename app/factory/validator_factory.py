from app.models.enums import JobType
from app.validators.base_validator import BaseValidator
from app.validators.blur_validator import BlurValidator
from app.validators.gps_validator import GPSValidator
from app.validators.duplicate_validator import DuplicateValidator
from app.validators.timestamp_validator import TimestampValidator


class ValidatorFactory:

    _validators: dict[JobType, type[BaseValidator]] = {
        JobType.BLUR_CHECK: BlurValidator,
        JobType.GPS_CHECK: GPSValidator,
        JobType.DUPLICATE_CHECK: DuplicateValidator,
        JobType.TIMESTAMP_ANOMALY_CHECK: TimestampValidator,
    }

    @classmethod
    def get_validator(cls, job_type: JobType) -> BaseValidator:

        validator_class = cls._validators.get(job_type)

        if validator_class is None:
            raise ValueError(f"Unsupported job type: {job_type}")

        return validator_class()