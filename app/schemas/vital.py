from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class VitalReadingCreate(BaseModel):
    type: str = Field(..., description="heart_rate | spo2 | sleep | steps | sedentary_min | fall_event | blood_pressure | temperature | glucose")
    value: float
    value_secondary: Optional[float] = None
    measured_at: datetime
    source: str = "manual"
    meta: Optional[Dict[str, Any]] = None


class VitalReadingBatchItem(BaseModel):
    type: str
    value: float
    value_secondary: Optional[float] = None
    measured_at: datetime
    meta: Optional[Dict[str, Any]] = None


class VitalBatchIngestRequest(BaseModel):
    readings: List[VitalReadingBatchItem]


class VitalReadingResponse(BaseModel):
    id: str
    patient_id: str
    type: str
    value: float
    value_secondary: Optional[float] = None
    measured_at: datetime
    source: str
    meta: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class LatestVitalDTO(BaseModel):
    type: str
    value: float
    measured_at: datetime
    in_range: bool = True


class VitalPointDTO(BaseModel):
    ts: datetime
    value: float
    min: Optional[float] = None
    max: Optional[float] = None


class VitalThresholdConfig(BaseModel):
    type: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class VitalThresholdResponse(BaseModel):
    id: str
    patient_id: str
    type: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class VitalSeriesResponse(BaseModel):
    type: str
    points: List[VitalPointDTO] = []
    threshold: Optional[Dict[str, Any]] = None


class SummaryHighlightDTO(BaseModel):
    icon_key: str = "heart"
    icon: str = "heart"
    label: str
    value: str


class TodaySummaryResponse(BaseModel):
    wellbeing_status: str = "ok"  # ok | warning | attention
    date: datetime
    summary: str = "El paciente se encuentra en estado estable y normal."
    top_reason: Optional[str] = "Estado estable"
    active_alerts_count: int = 0
    adherence_pct: int = 95
    highlights: List[SummaryHighlightDTO] = [
        SummaryHighlightDTO(icon_key="heart", icon="heart", label="Ritmo cardíaco", value="72 lpm"),
        SummaryHighlightDTO(icon_key="steps", icon="steps", label="Pasos", value="2.400"),
        SummaryHighlightDTO(icon_key="medication", icon="medication", label="Adherencia", value="95%")
    ]
    latest_vitals: List[Dict[str, Any]] = []


class WellbeingSummaryResponse(BaseModel):
    patient_id: str
    status: str  # ok | warning | attention
    reason: str
    last_vitals: Dict[str, Any]
    active_alerts_count: int
    medication_adherence_pct: float
