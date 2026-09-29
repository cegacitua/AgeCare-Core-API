from typing import Optional, Any
from sqlalchemy import String, Integer, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import ModelMixin


class AssistantConversation(Base, ModelMixin):
    __tablename__ = "assistant_conversations"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="Consulta sobre el expediente", nullable=False)


class AssistantMessage(Base, ModelMixin):
    __tablename__ = "assistant_messages"

    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("assistant_conversations.id", ondelete="CASCADE"), nullable=False)
    sender: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant
    text: Mapped[str] = mapped_column(String(4000), nullable=False)
    sources: Mapped[Optional[Any]] = mapped_column(JSON, default=list, nullable=True)


class ChatMessage(Base, ModelMixin):
    __tablename__ = "chat_messages"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Null if system / AI
    kind: Mapped[str] = mapped_column(String(20), default="text", nullable=False)  # text | audio | photo
    text: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    media_blob_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class ChatReadPointer(Base, ModelMixin):
    __tablename__ = "chat_read_pointers"
    __table_args__ = (
        UniqueConstraint("patient_id", "user_id", name="uq_patient_user_read_pointer"),
    )

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    last_read_message_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
