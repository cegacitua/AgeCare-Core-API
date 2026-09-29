from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class MedicationCreate(BaseModel):
    name: str
    dose: str
    instructions: Optional[str] = None
    times: List[str]  # e.g. ["08:00", "20:00"]
    days_of_week: Optional[List[int]] = [0, 1, 2, 3, 4, 5, 6]
    start_date: date
    end_date: Optional[date] = None
    grace_window_min: int = 60
    prescribed_by: Optional[str] = None


class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    dose: Optional[str] = None
    instructions: Optional[str] = None
    times: Optional[List[str]] = None
    days_of_week: Optional[List[int]] = None
    end_date: Optional[date] = None
    grace_window_min: Optional[int] = None


class MedicationResponse(BaseModel):
    id: str
    medication_id: Optional[str] = None
    patient_id: str
    name: str
    dose: str
    unit: str = "mg"
    form: str = "comprimido"
    schedule: List[str] = ["08:00"]
    instructions: Optional[str] = None
    times: List[str] = ["08:00"]
    days_of_week: Optional[List[int]] = None
    start_date: date
    end_date: Optional[date] = None
    grace_window_min: int = 60
    prescribed_by: Optional[str] = None
    discontinued_at: Optional[datetime] = None
    active: bool = True

    model_config = ConfigDict(from_attributes=True)


class ScheduledDoseResponse(BaseModel):
    id: str
    dose_id: Optional[str] = None
    medication_id: str
    medication_name: Optional[str] = None
    dose: Optional[str] = "50"
    unit: str = "mg"
    patient_id: str
    scheduled_at: datetime
    status: str  # pending | taken | postponed | missed
    logged_by: Optional[str] = None
    logged_at: Optional[datetime] = None
    reason: Optional[str] = None
    postponed_until: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LogDoseRequest(BaseModel):
    status: str = Field(..., description="taken | postponed | missed")
    reason: Optional[str] = None
    logged_at: Optional[datetime] = None
    note: Optional[str] = None
    postponed_until: Optional[datetime] = None


class AdherenceMetricsResponse(BaseModel):
    pct: int = 95
    period_days: int = 7
    total_scheduled: int = 14
    taken_count: int = 13
    missed_count: int = 1
    postponed_count: int = 0
    adherence_rate_pct: float = 95.0
    by_day: List[Dict[str, Any]] = [
        {"date": "2026-09-28T00:00:00Z", "pct": 95.0}
    ]
    by_medication: List[Dict[str, Any]] = [
        {"medication_id": "m-1", "medication_name": "Losartán", "pct": 95.0}
    ]
