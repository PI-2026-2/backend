from datetime import datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class PatientLink(SQLModel, table=True):
    __tablename__ = "patient_links"
    patient_id: int = Field(foreign_key="usuarios.id", primary_key=True)
    therapist_id: int = Field(foreign_key="usuarios.id", index=True)
    diagnosis: str = ""
    goal: str = ""
    risk: str = "baixo"


class ClinicalNote(SQLModel, table=True):
    __tablename__ = "clinical_notes"
    id: int | None = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="usuarios.id", index=True)
    therapist_id: int = Field(foreign_key="usuarios.id")
    title: str
    text: str
    created_at: datetime
    updated_at: datetime | None = None


class ChatEntry(SQLModel, table=True):
    __tablename__ = "chat_entries"
    id: int | None = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="usuarios.id", index=True)
    therapist_id: int = Field(foreign_key="usuarios.id")
    sender_id: int = Field(foreign_key="usuarios.id")
    text: str
    created_at: datetime


class CardProgram(SQLModel, table=True):
    __tablename__ = "card_programs"
    id: int | None = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="usuarios.id", index=True)
    therapist_id: int = Field(foreign_key="usuarios.id")
    card_ids: list[int] = Field(sa_column=Column(JSON, nullable=False))
    started_at: datetime


class CardResponse(SQLModel, table=True):
    __tablename__ = "card_responses"
    id: int | None = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="usuarios.id", index=True)
    card_id: int = Field(foreign_key="cartas.id")
    mode: str
    answer: str
    note: str | None = None
    created_at: datetime
