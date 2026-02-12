from typing import List
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CreateSessionRequest(BaseModel):
    host_name: str = Field(min_length=1, max_length=64)
    cuisine: str | None = Field(default=None, max_length=64)
    price: str | None = Field(default=None, max_length=16)
    radius_meters: int | None = Field(default=None, ge=1, le=40000)
    location_text: str | None = Field(default=None, max_length=256)


class JoinSessionRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=64)


class StartSessionRequest(BaseModel):
    host_name: str = Field(min_length=1, max_length=64)


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    room_code: str
    host_name: str
    status: str
    cuisine: str | None
    price: str | None
    radius_meters: int | None
    location_text: str | None
    participants: List[str]


class RestaurantCard(BaseModel):
    id: int
    name: str
    image_url: str | None
    address: str | None
    price: str | None
    rating: float | None
    review_count: int | None


class NextRestaurantResponse(BaseModel):
    restaurant: RestaurantCard | None


class VoteRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=64)
    restaurant_id: int = Field(gt=0)
    decision: Literal["yes", "no"]


class VoteResponse(BaseModel):
    duplicate: bool
    matched: bool
    matched_restaurant_id: int | None
    total_participants: int
    votes_submitted_for_restaurant: int
    yes_votes_for_restaurant: int
    next_restaurant: RestaurantCard | None
