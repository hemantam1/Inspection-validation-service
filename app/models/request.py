from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import (
    EvidenceType,
    JobType,
    InspectionAreaType,
)


class RegisteredLocation(BaseModel):
    latitude: float
    longitude: float


class Evidence(BaseModel):

    evidenceId: str
    evidenceType: EvidenceType

    fileUrl: str
    mimeType: str
    fileSize: int

    capturedAt: datetime

    latitude: float
    longitude: float
    gpsAccuracyM: float


class ValidationContext(BaseModel):

    taskId: str
    questionId: str

    registeredLocation: RegisteredLocation | None = None

    referenceEvidenceUrls: list[str] = Field(default_factory=list)

    expectedText: str | None = None

    priorStepCapturedAt: datetime | None = None

    taskStartedAt: datetime | None = None
    
    inspectionAreaType: InspectionAreaType


class ValidationRequest(BaseModel):
    jobId: str

    jobType: JobType

    evidence: Evidence

    context: ValidationContext

    requestJson: dict[str, Any] = Field(default_factory=dict)