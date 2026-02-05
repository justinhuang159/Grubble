from fastapi import FastAPI, HTTPException
from uuid import uuid4

from .schemas import CreateSessionRequest, SessionResponse, JoinSessionRequest

app = FastAPI()

SESSIONS = {}

@app.post("/sessions", response_model=SessionResponse)
def create_session(req: CreateSessionRequest):
    session_id = str(uuid4())
    SESSIONS[session_id] = {
        "id": session_id,
        "host_name": req.host_name,
        "participants": []
    }
    return SESSIONS[session_id]

@app.post("/sessions/{session_id}/join", response_model=SessionResponse)
def join_session(session_id: str, req: JoinSessionRequest):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["participants"].append(req.user_name)
    return session

@app.get("/sessions", response_model=list[SessionResponse])
def list_sessions():
    return list(SESSIONS.values())