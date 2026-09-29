from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AskAssistantRequest(BaseModel):
    conversation_id: Optional[str] = None
    question: str = Field(..., min_length=1)


class AssistantSource(BaseModel):
    title: str
    category: str
    date: Optional[str] = None


class AssistantMessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender: str  # user | assistant
    text: str
    sources: Optional[List[AssistantSource]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssistantConversationResponse(BaseModel):
    id: str
    patient_id: str
    user_id: str
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SendChatMessageRequest(BaseModel):
    kind: str = "text"  # text | audio | photo
    text: Optional[str] = None
    media_blob_path: Optional[str] = None
    duration_sec: Optional[int] = None


class ChatMessageResponse(BaseModel):
    id: str
    patient_id: str
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    kind: str
    text: Optional[str] = None
    media_blob_path: Optional[str] = None
    duration_sec: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarkReadPointerRequest(BaseModel):
    last_read_message_id: str
