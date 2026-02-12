import random
import string
from collections.abc import Generator
import os
from collections import defaultdict

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Participant, Session as SessionModel
from .schemas import CreateSessionRequest, JoinSessionRequest, SessionResponse, StartSessionRequest

app = FastAPI()

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, room_code: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[room_code].add(websocket)

    def disconnect(self, room_code: str, websocket: WebSocket) -> None:
        room_connections = self._connections.get(room_code)
        if not room_connections:
            return
        room_connections.discard(websocket)
        if not room_connections:
            self._connections.pop(room_code, None)

    async def broadcast(self, room_code: str, message: dict) -> None:
        room_connections = list(self._connections.get(room_code, set()))
        for connection in room_connections:
            try:
                await connection.send_json(message)
            except RuntimeError:
                self.disconnect(room_code, connection)


ws_manager = ConnectionManager()


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
        status=session.status,
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


@app.post("/sessions/{room_code}/start", response_model=SessionResponse)
async def start_session(room_code: str, req: StartSessionRequest, db: Session = Depends(get_db)):
    session = db.scalar(select(SessionModel).where(SessionModel.room_code == room_code))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if req.host_name != session.host_name:
        raise HTTPException(status_code=403, detail="Only the host can start this session")
    if session.status != "waiting":
        raise HTTPException(status_code=409, detail="Session can only be started from waiting state")

    session.status = "active"
    db.commit()
    db.refresh(session)
    response = build_response(session)
    await ws_manager.broadcast(
        room_code,
        {"event": "session_started", "session": response.model_dump()},
    )
    return response


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


@app.websocket("/ws/sessions/{room_code}")
async def session_updates_socket(websocket: WebSocket, room_code: str):
    db = SessionLocal()
    try:
        session = db.scalar(select(SessionModel).where(SessionModel.room_code == room_code))
        if not session:
            await websocket.close(code=1008, reason="Session not found")
            return
    finally:
        db.close()

    await ws_manager.connect(room_code, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(room_code, websocket)
