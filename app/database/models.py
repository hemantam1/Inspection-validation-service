from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func

from app.database.connection import Base


class ValidationRecord(Base):
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(String, nullable=False)
    job_type = Column(String, nullable=False)

    status = Column(String, nullable=False)

    confidence_score = Column(Integer, nullable=False)

    result_json = Column(JSON, nullable=False)

    risk_flags = Column(JSON, nullable=False)

    error = Column(JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )