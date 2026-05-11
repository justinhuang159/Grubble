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


class PhotoItem(BaseModel):
    url: str
    caption: str | None = None


class HoursItem(BaseModel):
    day: str
    hours: str


class PopularDishItem(BaseModel):
    display_name: str
    review_count: int
    photo_url: str | None = None
    photo_count: int = 0


class RestaurantCard(BaseModel):
    id: int
    name: str
    image_url: str | None
    address: str | None
    price: str | None
    rating: float | None
    review_count: int | None
    categories: list[str] = []
    photos: list[PhotoItem] = []
    hours: list[HoursItem] | None = None
    yelp_url: str | None = None
    phone: str | None = None
    short_address: str | None = None
    popular_dishes: list[PopularDishItem] | None = None


class NextRestaurantResponse(BaseModel):
    restaurant: RestaurantCard | None
    total_participants: int = 0
    yes_votes: int = 0
    total_votes: int = 0


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
    next_yes_votes: int = 0
    next_total_votes: int = 0


class SessionResultItem(BaseModel):
    restaurant: RestaurantCard
    yes_votes: int
    total_votes: int


class SessionResultsResponse(BaseModel):
    total_participants: int
    results: List[SessionResultItem]
