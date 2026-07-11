from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import JobStatus, JobType, RiskEventType, RiskSeverity


class RiskFlag(BaseModel):

    riskEventType: RiskEventType
    severity: RiskSeverity
    score: int
    reason: str


class ErrorInfo(BaseModel):

    code: str
    message: str
    details: str | None = None


class ValidationResponse(BaseModel):

    jobId: str

    status: JobStatus

    resultType: JobType

    confidenceScore: int

    resultJson: dict[str, Any]

    riskFlags: list[RiskFlag] = Field(default_factory=list)

    error: ErrorInfo | None = None