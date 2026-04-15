from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime


class IngestRequest(BaseModel):
    sensor_id: str = Field(..., min_length=1)
    readings: Dict[str, float]


class IngestResponse(BaseModel):
    status: str
    message: str
    sensor_id: str
    timestamp: datetime


class StatusResponse(BaseModel):
    status: str
    uptime_seconds: float
    active_sensors: int
    total_readings: int
    last_update: Optional[datetime]


class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: datetime