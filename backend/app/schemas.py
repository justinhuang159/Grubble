from typing import List

from pydantic import BaseModel, ConfigDict, Field


class CreateSessionRequest(BaseModel):
    host_name: str = Field(min_length=1, max_length=64)


class JoinSessionRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=64)


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    room_code: str
    host_name: str
    participants: List[str]
