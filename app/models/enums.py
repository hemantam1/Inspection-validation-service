from enum import Enum


class JobType(str, Enum):

    BLUR_CHECK = "BLUR_CHECK"
    GPS_CHECK = "GPS_CHECK"
    DUPLICATE_CHECK = "DUPLICATE_CHECK"
    TIMESTAMP_ANOMALY_CHECK = "TIMESTAMP_ANOMALY_CHECK"


class JobStatus(str, Enum):
    
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EvidenceType(str, Enum):

    PHOTO = "PHOTO"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"


class RiskSeverity(str, Enum):

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskEventType(str, Enum):

    BLUR_IMAGE = "BLUR_IMAGE"
    GPS_MISMATCH = "GPS_MISMATCH"
    DUPLICATE_IMAGE = "DUPLICATE_IMAGE"
    FAST_SUBMISSION = "FAST_SUBMISSION"