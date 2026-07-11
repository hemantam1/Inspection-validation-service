from typing import Any

from pydantic import BaseModel, Field

from app.models.response import ErrorInfo, RiskFlag


class ValidationResult(BaseModel):

    confidenceScore: int = Field(..., ge=0, le=100)

    result: dict[str, Any]

    riskFlags: list[RiskFlag] = Field(default_factory=list)

    error: ErrorInfo | None = None