import random
import string
from collections.abc import Generator

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Participant, Session as SessionModel
from .schemas import CreateSessionRequest, JoinSessionRequest, SessionResponse

app = FastAPI()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def build_response(session: SessionModel) -> SessionResponse:
    participants = [participant.user_name for participant in session.participants]
    return SessionResponse(
        id=session.id,
        room_code=session.room_code,
        host_name=session.host_name,
        participants=participants,
    )


def generate_room_code(db: Session, length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(50):
        code = "".join(random.choice(alphabet) for _ in range(length))
        existing = db.scalar(select(SessionModel).where(SessionModel.room_code == code))
        if existing is None:
            return code
    raise HTTPException(status_code=500, detail="Failed to generate unique room code")


@app.post("/sessions", response_model=SessionResponse)
def create_session(req: CreateSessionRequest, db: Session = Depends(get_db)):
    room_code = generate_room_code(db)
    session = SessionModel(room_code=room_code, host_name=req.host_name, status="waiting")
    session.participants.append(Participant(user_name=req.host_name))
    db.add(session)
    db.commit()
    db.refresh(session)
    return build_response(session)


@app.post("/sessions/{room_code}/join", response_model=SessionResponse)
def join_session(room_code: str, req: JoinSessionRequest, db: Session = Depends(get_db)):
    session = db.scalar(select(SessionModel).where(SessionModel.room_code == room_code))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    duplicate = db.scalar(
        select(Participant).where(
            Participant.session_id == session.id,
            Participant.user_name == req.user_name,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Participant name already exists in this session")

    session.participants.append(Participant(user_name=req.user_name))
    db.commit()
    db.refresh(session)
    return build_response(session)


@app.get("/sessions/{room_code}", response_model=SessionResponse)
def get_session(room_code: str, db: Session = Depends(get_db)):
    session = db.scalar(select(SessionModel).where(SessionModel.room_code == room_code))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return build_response(session)


@app.get("/sessions", response_model=list[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.scalars(select(SessionModel)).all()
    return [build_response(session) for session in sessions]
