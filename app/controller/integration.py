from datetime import date, datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field as BodyField
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database import SessionDep
from app.model.Usuario import UsuarioCadastro
from app.model.enums import TipoUsuarioEnum
from app.model.integration import CardProgram, CardResponse, ChatEntry, ClinicalNote, PatientLink
from app.model.tables import Baralhos, Cartas, Etiquetas, Usuarios
from app.service.auth_service import AuthService

router = APIRouter(tags=["Integração"])
CurrentUser = Annotated[Usuarios, Depends(AuthService().obter_usuario_atual)]


class PatientCreate(UsuarioCadastro):
    diagnosis: str = ""
    goal: str = ""


class NoteInput(BaseModel):
    title: str = BodyField(min_length=1)
    text: str = BodyField(min_length=1)


class MessageInput(BaseModel):
    patient_id: int | None = None
    text: str = BodyField(min_length=1)


class ProgramInput(BaseModel):
    patient_id: int
    card_ids: list[int] = BodyField(min_length=7, max_length=7)


class ResponseInput(BaseModel):
    patient_id: int | None = None
    card_id: int
    mode: Literal["daily", "session"]
    answer: str = BodyField(min_length=1)
    note: str | None = None


def therapist_only(user: Usuarios) -> None:
    if user.tipo != TipoUsuarioEnum.TERAPEUTA:
        raise HTTPException(403, "Acesso exclusivo do terapeuta")


def patient_link(session: SessionDep, user: Usuarios, patient_id: int | None) -> PatientLink:
    if user.tipo == TipoUsuarioEnum.PACIENTE:
        link = session.get(PatientLink, user.id)
    elif user.tipo == TipoUsuarioEnum.TERAPEUTA and patient_id is not None:
        link = session.get(PatientLink, patient_id)
        if link and link.therapist_id != user.id:
            link = None
    else:
        raise HTTPException(403, "Acesso não permitido")
    if link is None:
        raise HTTPException(404, "Vínculo terapêutico não encontrado")
    return link


def patient_data(link: PatientLink | None, patient: Usuarios) -> dict:
    today = date.today()
    age = today.year - patient.data_nascimento.year - (
        (today.month, today.day) < (patient.data_nascimento.month, patient.data_nascimento.day)
    )
    return {
        "id": patient.id, "name": patient.nome, "age": age,
        "phone": patient.telefone, "email": patient.email,
        "diagnosis": link.diagnosis if link else "",
        "goal": link.goal if link else "",
        "risk": link.risk if link else "baixo",
        "therapist_id": link.therapist_id if link else None,
    }


def utc_text(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc).isoformat() if value.tzinfo is None else value.astimezone(timezone.utc).isoformat()


def note_data(note: ClinicalNote) -> dict:
    return {
        "id": note.id, "patient_id": note.patient_id, "title": note.title,
        "text": note.text, "created_at": utc_text(note.created_at),
        "updated_at": utc_text(note.updated_at),
    }


def message_data(entry: ChatEntry) -> dict:
    return {
        "id": entry.id, "patient_id": entry.patient_id,
        "sender": "patient" if entry.sender_id == entry.patient_id else "therapist",
        "text": entry.text, "created_at": utc_text(entry.created_at),
    }


def program_data(program: CardProgram) -> dict:
    return {
        "id": program.id, "patient_id": program.patient_id,
        "card_ids": program.card_ids, "started_at": utc_text(program.started_at),
    }


def response_data(response: CardResponse) -> dict:
    return {
        "id": response.id, "patient_id": response.patient_id,
        "card_id": response.card_id, "mode": response.mode,
        "answer": response.answer, "note": response.note,
        "created_at": utc_text(response.created_at),
    }


@router.get("/patients")
def list_patients(user: CurrentUser, session: SessionDep):
    if user.tipo == TipoUsuarioEnum.TERAPEUTA:
        links = session.exec(select(PatientLink).where(PatientLink.therapist_id == user.id)).all()
        return [patient_data(link, session.get(Usuarios, link.patient_id)) for link in links]
    if user.tipo == TipoUsuarioEnum.PACIENTE:
        return [patient_data(session.get(PatientLink, user.id), user)]
    raise HTTPException(403, "Acesso não permitido")


@router.post("/patients", status_code=201)
def create_patient(payload: PatientCreate, user: CurrentUser, session: SessionDep):
    therapist_only(user)
    if payload.tipo != "PACIENTE":
        raise HTTPException(422, "O cadastro deve ser de paciente")
    patient = Usuarios(
        nome=payload.nome.strip(), telefone=payload.telefone.strip(),
        data_nascimento=payload.data_nascimento, genero=payload.genero,
        email=payload.email.strip().lower(),
        senha_hash=AuthService().obter_hash_senha(payload.senha),
        tipo=TipoUsuarioEnum.PACIENTE,
    )
    try:
        session.add(patient)
        session.flush()
        link = PatientLink(
            patient_id=patient.id, therapist_id=user.id,
            diagnosis=payload.diagnosis.strip(), goal=payload.goal.strip(),
        )
        session.add(link)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "E-mail já cadastrado")
    session.refresh(patient)
    return patient_data(link, patient)


@router.get("/patients/{patient_id}/notes")
def list_notes(patient_id: int, user: CurrentUser, session: SessionDep):
    therapist_only(user)
    patient_link(session, user, patient_id)
    notes = session.exec(select(ClinicalNote).where(ClinicalNote.patient_id == patient_id)
                         .order_by(ClinicalNote.created_at.desc())).all()
    return [note_data(note) for note in notes]


@router.post("/patients/{patient_id}/notes", status_code=201)
def create_note(patient_id: int, payload: NoteInput, user: CurrentUser, session: SessionDep):
    therapist_only(user)
    patient_link(session, user, patient_id)
    note = ClinicalNote(patient_id=patient_id, therapist_id=user.id,
                        title=payload.title.strip(), text=payload.text.strip(),
                        created_at=datetime.now(timezone.utc))
    session.add(note)
    session.commit()
    session.refresh(note)
    return note_data(note)


@router.put("/patients/{patient_id}/notes/{note_id}")
def update_note(patient_id: int, note_id: int, payload: NoteInput,
                user: CurrentUser, session: SessionDep):
    therapist_only(user)
    patient_link(session, user, patient_id)
    note = session.get(ClinicalNote, note_id)
    if note is None or note.patient_id != patient_id or note.therapist_id != user.id:
        raise HTTPException(404, "Evolução não encontrada")
    note.title = payload.title.strip()
    note.text = payload.text.strip()
    note.updated_at = datetime.now(timezone.utc)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note_data(note)


@router.get("/messages")
def list_messages(user: CurrentUser, session: SessionDep,
                  patient_id: int | None = Query(default=None)):
    link = patient_link(session, user, patient_id)
    messages = session.exec(select(ChatEntry).where(ChatEntry.patient_id == link.patient_id)
                            .order_by(ChatEntry.created_at, ChatEntry.id)).all()
    return [message_data(entry) for entry in messages]


@router.get("/conversations")
def list_conversations(user: CurrentUser, session: SessionDep):
    if user.tipo == TipoUsuarioEnum.TERAPEUTA:
        entries = session.exec(select(ChatEntry).where(ChatEntry.therapist_id == user.id)
                               .order_by(ChatEntry.created_at, ChatEntry.id)).all()
    elif user.tipo == TipoUsuarioEnum.PACIENTE:
        entries = session.exec(select(ChatEntry).where(ChatEntry.patient_id == user.id)
                               .order_by(ChatEntry.created_at, ChatEntry.id)).all()
    else:
        raise HTTPException(403, "Acesso não permitido")
    return [message_data(entry) for entry in entries]


@router.post("/messages", status_code=201)
def send_message(payload: MessageInput, user: CurrentUser, session: SessionDep):
    link = patient_link(session, user, payload.patient_id)
    entry = ChatEntry(patient_id=link.patient_id, therapist_id=link.therapist_id,
                      sender_id=user.id, text=payload.text.strip(),
                      created_at=datetime.now(timezone.utc))
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return message_data(entry)


@router.get("/catalog")
def catalog(user: CurrentUser, session: SessionDep):
    themes = session.exec(select(Etiquetas).order_by(Etiquetas.nome)).all()
    decks = session.exec(select(Baralhos).order_by(Baralhos.nome)).all()
    cards = session.exec(select(Cartas).where(Cartas.ativa == True)).all()
    return {
        "themes": [{"id": f"t{theme.id}", "name": theme.nome, "description": ""} for theme in themes],
        "decks": [{"id": f"d{deck.id}", "themeId": f"t{deck.etiqueta_id}",
                   "name": deck.nome, "description": ""} for deck in decks],
        "cards": [{"id": f"c{card.id}", "deckId": f"d{card.baralho_id}",
                   "title": card.frente, "theme": card.frente,
                   "classification": "Sem classificação", "prompt": card.verso} for card in cards],
    }


@router.get("/programs")
def list_programs(user: CurrentUser, session: SessionDep,
                  patient_id: int | None = Query(default=None)):
    link = patient_link(session, user, patient_id)
    program = session.exec(select(CardProgram).where(CardProgram.patient_id == link.patient_id)
                           .order_by(CardProgram.started_at.desc(), CardProgram.id.desc())).first()
    return [program_data(program)] if program else []


@router.post("/programs", status_code=201)
def create_program(payload: ProgramInput, user: CurrentUser, session: SessionDep):
    therapist_only(user)
    patient_link(session, user, payload.patient_id)
    if len(set(payload.card_ids)) != 7:
        raise HTTPException(422, "Selecione sete cartas diferentes")
    cards = [session.get(Cartas, card_id) for card_id in payload.card_ids]
    if any(card is None or not card.ativa for card in cards):
        raise HTTPException(422, "Carta indisponível")
    if len({card.baralho_id for card in cards}) != 1 or len({card.frente for card in cards}) != 7:
        raise HTTPException(422, "As cartas devem ter assuntos distintos do mesmo baralho")
    program = CardProgram(patient_id=payload.patient_id, therapist_id=user.id,
                          card_ids=payload.card_ids, started_at=datetime.now(timezone.utc))
    session.add(program)
    session.commit()
    session.refresh(program)
    return program_data(program)


@router.get("/responses")
def list_responses(user: CurrentUser, session: SessionDep,
                   patient_id: int | None = Query(default=None)):
    link = patient_link(session, user, patient_id)
    responses = session.exec(select(CardResponse).where(CardResponse.patient_id == link.patient_id)
                             .order_by(CardResponse.created_at.desc(), CardResponse.id.desc())).all()
    return [response_data(response) for response in responses]


@router.post("/responses", status_code=201)
def create_response(payload: ResponseInput, user: CurrentUser, session: SessionDep):
    link = patient_link(session, user, payload.patient_id)
    card = session.get(Cartas, payload.card_id)
    if card is None or not card.ativa:
        raise HTTPException(422, "Carta indisponível")
    if payload.mode == "daily":
        if user.tipo != TipoUsuarioEnum.PACIENTE:
            raise HTTPException(403, "Somente o paciente pode responder à carta do dia")
        program = session.exec(select(CardProgram).where(CardProgram.patient_id == link.patient_id)
                               .order_by(CardProgram.started_at.desc(), CardProgram.id.desc())).first()
        if program is None:
            raise HTTPException(422, "Não há jogo de sete dias ativo")
        day = (datetime.now(timezone.utc).date() - program.started_at.date()).days
        if day < 0 or day > 6 or program.card_ids[day] != payload.card_id:
            raise HTTPException(422, "Esta não é a carta do dia")
    elif user.tipo != TipoUsuarioEnum.TERAPEUTA:
        raise HTTPException(403, "Somente o terapeuta pode registrar a sessão")
    response = CardResponse(patient_id=link.patient_id, card_id=payload.card_id,
                            mode=payload.mode, answer=payload.answer.strip(),
                            note=payload.note, created_at=datetime.now(timezone.utc))
    session.add(response)
    session.commit()
    session.refresh(response)
    return response_data(response)
