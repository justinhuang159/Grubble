# schemas.py
from pydantic import BaseModel
from typing import List

# Request to create a session
class CreateSessionRequest(BaseModel):
    host_name: str

# Response when a session is created or returned
class SessionResponse(BaseModel):
    id: str
    host_name: str
    participants: List[str]

# Request to join a session
class JoinSessionRequest(BaseModel):
    user_name: str

# Response representing a user (optional for future use)
class UserResponse(BaseModel):
    id: str
    user_name: str