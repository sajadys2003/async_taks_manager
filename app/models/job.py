from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import declarative_base
from app.models.enums import JobStatus

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, index=True)
    payload = Column(String, nullable=True)
    time_created = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    time_started = Column(DateTime(timezone=True), nullable=True)
    time_done = Column(DateTime(timezone=True), nullable=True)