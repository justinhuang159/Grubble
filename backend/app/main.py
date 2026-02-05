from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4

app = FastAPI()

# In-memory "DB"
SESSIONS = {}
USERS = {}

# Pydantic schemas
class CreateSessionRequest(BaseModel):
    host_name: str

class SessionResponse(BaseModel):
    id: str
    host_name: str
    participants: list[str]

class JoinSessionRequest(BaseModel):
    user_name: str

class UserResponse(BaseModel):
    id: str
    user_name: str

# Endpoints
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
        # FastAPI handles proper error responses
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")

    # Ensure participants list exists
    if "participants" not in session:
        session["participants"] = []

    session["participants"].append(req.user_name)
    return session