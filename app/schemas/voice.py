from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class VoiceUploadAcceptedResponse(BaseModel):
    jobId: str
    status: str = "processing"
    estimatedTimeSeconds: int = 5


class ExtractedClinicalData(BaseModel):
    sentiment: Optional[str] = "neutral"  # positive | neutral | negative
    alerts: Optional[List[str]] = Field(default_factory=list)
    vitalSignMentions: Optional[Dict[str, Any]] = Field(default_factory=dict)


class VoiceTranscriptionResponse(BaseModel):
    jobId: str
    status: str  # processing | completed | failed
    transcription: Optional[str] = None
    extractedData: Optional[ExtractedClinicalData] = None
