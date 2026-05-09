import random
import string
from collections.abc import Generator
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import case, delete, func, select
from sqlalchemy.orm import Session

from . import config  # noqa: F401
from .database import SessionLocal
from .integrations.yelp_client import MissingRapidAPIConfigError, YelpClient, YelpClientError
from .models import Participant, Restaurant, Session as SessionModel, Vote, YelpQueryCache
from .schemas import (
    CreateSessionRequest,
    HoursItem,
    JoinSessionRequest,
    NextRestaurantResponse,
    PhotoItem,
    RestaurantCard,
    SessionResponse,
    SessionResultItem,
    SessionResultsResponse,
    StartSessionRequest,
    VoteRequest,
    VoteResponse,
)

app = FastAPI()


def get_allowed_frontend_origins() -> list[str]:
    raw_origins = os.getenv("FRONTEND_ORIGINS") or os.getenv("FRONTEND_ORIGIN", "")
    configured_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    defaults = ["http://127.0.0.1:5173", "http://localhost:5173"]
    return list(dict.fromkeys([*configured_origins, *defaults]))


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_frontend_origins(),
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
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
        cuisine=session.cuisine,
        price=session.price,
        radius_meters=session.radius_meters,
        location_text=session.location_text,
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


def is_mock_yelp_enabled() -> bool:
    return os.getenv("USE_MOCK_YELP", "").strip().lower() in {"1", "true", "yes", "on"}


def build_query_key(*, term: str, location_text: str, price: str | None, radius_meters: int | None) -> str:
    normalized_price = (price or "").strip()
    normalized_radius = str(radius_meters or "")
    return "|".join([term.strip().lower(), location_text.strip().lower(), normalized_price, normalized_radius])


def get_mock_businesses(term: str, location_text: str) -> list[dict]:
    return [
        {
            "id": "mock-1",
            "name": f"{term.title()} House",
            "image_url": None,
            "location": {"display_address": [f"123 Main St", location_text]},
            "coordinates": {"latitude": 37.7749, "longitude": -122.4194},
            "price": "$$",
            "rating": 4.4,
            "review_count": 180,
        },
        {
            "id": "mock-2",
            "name": f"{term.title()} Corner",
            "image_url": None,
            "location": {"display_address": [f"456 Market St", location_text]},
            "coordinates": {"latitude": 37.7849, "longitude": -122.4094},
            "price": "$",
            "rating": 4.1,
            "review_count": 95,
        },
        {
            "id": "mock-3",
            "name": f"{term.title()} Alley",
            "image_url": None,
            "location": {"display_address": [f"789 Franklin St", location_text]},
            "coordinates": {"latitude": 37.7949, "longitude": -122.4294},
            "price": "$$$",
            "rating": 4.7,
            "review_count": 60,
        }
    ]


def is_cache_row_fresh(created_at: datetime, cutoff: datetime) -> bool:
    row_time = created_at
    if row_time.tzinfo is None:
        row_time = row_time.replace(tzinfo=timezone.utc)
    return row_time >= cutoff


def get_yelp_client_from_env() -> YelpClient:
    api_key = os.getenv("RAPIDAPI_KEY")
    api_host = os.getenv("RAPIDAPI_HOST")
    base_url = os.getenv("RAPIDAPI_YELP_BASE_URL", "https://yelp-business-api.p.rapidapi.com")
    if not api_key or not api_host:
        raise MissingRapidAPIConfigError("Missing RAPIDAPI_KEY or RAPIDAPI_HOST")
    return YelpClient(api_key=api_key, api_host=api_host, base_url=base_url)


def build_yelp_photo_url(photo: dict | None) -> str | None:
    if not isinstance(photo, dict):
        return None

    direct_url = photo.get("url") or photo.get("photo_url")
    if isinstance(direct_url, str) and direct_url.strip():
        return direct_url.strip()

    url_prefix = photo.get("url_prefix")
    url_suffix = photo.get("url_suffix")
    if isinstance(url_prefix, str) and isinstance(url_suffix, str) and url_prefix.strip() and url_suffix.strip():
        return f"{url_prefix.strip()}o{url_suffix.strip()}"

    return None


def extract_business_image_url(item: dict) -> str | None:
    primary_photo = item.get("primary_photo")
    if isinstance(primary_photo, str) and primary_photo.strip():
        return primary_photo.strip()

    primary_photo_url = build_yelp_photo_url(primary_photo if isinstance(primary_photo, dict) else None)
    if primary_photo_url:
        return primary_photo_url

    for key in ("photos", "menu_photos"):
        photos = item.get(key)
        if isinstance(photos, list):
            for photo in photos:
                photo_url = build_yelp_photo_url(photo if isinstance(photo, dict) else None)
                if photo_url:
                    return photo_url

    direct_fields = [
        item.get("image_url"),
        item.get("photo_url"),
    ]
    for value in direct_fields:
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def search_pexels_fallback_images(query: str, limit: int) -> list[str]:
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key or limit <= 0:
        return []

    url = os.getenv("PEXELS_API_BASE_URL", "https://api.pexels.com/v1").rstrip("/") + "/search"
    params = {"query": query, "per_page": min(limit, 20), "orientation": "landscape"}
    headers = {"Authorization": api_key}

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=headers, params=params)
        if response.status_code >= 400:
            return []
    except httpx.HTTPError:
        return []

    payload = response.json()
    photos = payload.get("photos")
    if not isinstance(photos, list):
        return []

    urls: list[str] = []
    for photo in photos:
        if not isinstance(photo, dict):
            continue
        src = photo.get("src")
        if not isinstance(src, dict):
            continue
        candidate = src.get("landscape") or src.get("large") or src.get("medium") or src.get("original")
        if isinstance(candidate, str) and candidate.strip():
            urls.append(candidate.strip())
        if len(urls) >= limit:
            break
    return urls


def cache_restaurants_for_session(db: Session, session: SessionModel) -> int:
    if not session.location_text:
        raise HTTPException(status_code=400, detail="location_text is required to start a session")

    term = session.cuisine or "restaurants"
    if is_mock_yelp_enabled():
        businesses = get_mock_businesses(term=term, location_text=session.location_text)
    else:
        try:
            cache_ttl_minutes = int(os.getenv("YELP_CACHE_TTL_MINUTES", "1440"))
        except ValueError:
            cache_ttl_minutes = 1440
        cache_cutoff = datetime.now(timezone.utc) - timedelta(minutes=cache_ttl_minutes)
        query_key = build_query_key(
            term=term,
            location_text=session.location_text,
            price=session.price,
            radius_meters=session.radius_meters,
        )
        cache_row = db.scalar(select(YelpQueryCache).where(YelpQueryCache.query_key == query_key))
        if cache_row and is_cache_row_fresh(cache_row.created_at, cache_cutoff) and isinstance(cache_row.results, list):
            businesses = cache_row.results
        else:
            client = get_yelp_client_from_env()
            businesses = client.search_businesses(
                term=term,
                location=session.location_text,
                price=session.price,
                radius_meters=session.radius_meters,
                limit=30,
            )
            if cache_row:
                cache_row.results = businesses
                cache_row.created_at = datetime.now(timezone.utc)
            else:
                db.add(
                    YelpQueryCache(
                        query_key=query_key,
                        term=term,
                        location_text=session.location_text,
                        price=session.price,
                        radius_meters=session.radius_meters,
                        results=businesses,
                    )
                )

    if not businesses:
        raise HTTPException(status_code=404, detail="No restaurants found for this session")

    fallback_query = f"{term} restaurant food"
    missing_image_count = sum(1 for item in businesses if extract_business_image_url(item) is None)
    fallback_image_urls = search_pexels_fallback_images(fallback_query, missing_image_count)

    db.execute(delete(Restaurant).where(Restaurant.session_id == session.id))
    for idx, item in enumerate(businesses):
        location = item.get("location") or {}
        coordinates = item.get("coordinates") or {}
        display_address = location.get("display_address")
        if isinstance(display_address, list):
            address = ", ".join(str(part) for part in display_address)
        else:
            address = location.get("address1")

        external_id = str(item.get("id") or item.get("alias") or f"generated-{idx}")
        image_url = extract_business_image_url(item)
        if image_url is None and fallback_image_urls:
            image_url = fallback_image_urls.pop(0)
        db.add(
            Restaurant(
                session_id=session.id,
                external_id=external_id,
                name=str(item.get("name") or "Unknown Restaurant"),
                image_url=image_url,
                address=address,
                lat=coordinates.get("latitude"),
                lng=coordinates.get("longitude"),
                price=item.get("price"),
                rating=item.get("rating"),
                review_count=item.get("review_count"),
                source_payload=item,
            )
        )
    return len(businesses)


def _fmt_time(t: str) -> str:
    h, m = int(t[:2]), int(t[2:])
    period = "AM" if h < 12 else "PM"
    h = h % 12 or 12
    return f"{h}:{m:02d} {period}"


def build_restaurant_card(restaurant: Restaurant) -> RestaurantCard:
    payload = restaurant.source_payload or {}

    raw_cats = payload.get("categories") or []
    categories = [c.get("name") or c.get("title") for c in raw_cats if c.get("name") or c.get("title")]

    raw_photos = payload.get("photos") or []
    photos: list[PhotoItem] = []
    for p in raw_photos[:6]:
        prefix = p.get("url_prefix", "")
        suffix = p.get("url_suffix", ".jpg")
        if prefix:
            photos.append(PhotoItem(url=f"{prefix}l{suffix}", caption=p.get("caption") or None))

    hours: list[HoursItem] | None = None
    raw_hours = payload.get("hours") or []
    if raw_hours:
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        regular = next((h for h in raw_hours if h.get("hours_type") == "REGULAR"), raw_hours[0])
        parsed = []
        for slot in regular.get("open") or []:
            start, end = slot.get("start", ""), slot.get("end", "")
            if start and end:
                parsed.append(HoursItem(
                    day=day_names[slot.get("day", 0) % 7],
                    hours=f"{_fmt_time(start)} – {_fmt_time(end)}",
                ))
        if parsed:
            hours = parsed

    alias = payload.get("alias")
    yelp_url = f"https://www.yelp.com/biz/{alias}" if alias else None

    phone = payload.get("localized_phone") or payload.get("phone") or None

    short_address = None
    addresses = payload.get("addresses") or {}
    primary = addresses.get("primary_language") or {}
    short_address = primary.get("short_form") or None

    return RestaurantCard(
        id=restaurant.id,
        name=restaurant.name,
        image_url=restaurant.image_url,
        address=restaurant.address,
        price=restaurant.price,
        rating=restaurant.rating,
        review_count=restaurant.review_count,
        categories=categories,
        photos=photos,
        hours=hours,
        yelp_url=yelp_url,
        phone=phone,
        short_address=short_address,
    )


def get_next_restaurant_for_user(db: Session, session_id: str, user_name: str) -> Restaurant | None:
    voted_restaurant_ids = select(Vote.restaurant_id).where(
        Vote.session_id == session_id,
        Vote.participant_name == user_name,
    )
    return db.scalar(
        select(Restaurant)
        .where(Restaurant.session_id == session_id, ~Restaurant.id.in_(voted_restaurant_ids))
        .order_by(Restaurant.id.asc())
        .limit(1)
    )


@app.post("/sessions", response_model=SessionResponse)
def create_session(req: CreateSessionRequest, db: Session = Depends(get_db)):
    room_code = generate_room_code(db)
    session = SessionModel(
        room_code=room_code,
        host_name=req.host_name,
        status="waiting",
        cuisine=req.cuisine,
        price=req.price,
        radius_meters=req.radius_meters,
        location_text=req.location_text,
    )
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

    try:
        cache_restaurants_for_session(db, session)
    except MissingRapidAPIConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except YelpClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    session.status = "active"
    db.commit()
    db.refresh(session)
    response = build_response(session)
    await ws_manager.broadcast(
        room_code,
        {"event": "session_started", "session": response.model_dump()},
    )
    return response


@app.get("/sessions/{room_code}/restaurants/next", response_model=NextRestaurantResponse)
def get_next_restaurant(room_code: str, user_name: str, db: Session = Depends(get_db)):
    session = db.scalar(select(SessionModel).where(SessionModel.room_code == room_code))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=409, detail="Session is not active")

    participant = db.scalar(
        select(Participant).where(
            Participant.session_id == session.id,
            Participant.user_name == user_name,
        )
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found in session")

    next_restaurant = get_next_restaurant_for_user(db, session.id, user_name)
    if not next_restaurant:
        return NextRestaurantResponse(restaurant=None)

    total_participants = db.scalar(
        select(func.count(Participant.id)).where(Participant.session_id == session.id)
    ) or 0
    yes_votes = db.scalar(
        select(func.count(Vote.id)).where(
            Vote.session_id == session.id,
            Vote.restaurant_id == next_restaurant.id,
            Vote.decision == "yes",
        )
    ) or 0
    total_votes = db.scalar(
        select(func.count(Vote.id)).where(
            Vote.session_id == session.id,
            Vote.restaurant_id == next_restaurant.id,
        )
    ) or 0

    return NextRestaurantResponse(
        restaurant=build_restaurant_card(next_restaurant),
        total_participants=total_participants,
        yes_votes=yes_votes,
        total_votes=total_votes,
    )


@app.post("/sessions/{room_code}/votes", response_model=VoteResponse)
async def submit_vote(room_code: str, req: VoteRequest, db: Session = Depends(get_db)):
    session = db.scalar(select(SessionModel).where(SessionModel.room_code == room_code))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=409, detail="Session is not active")

    participant = db.scalar(
        select(Participant).where(
            Participant.session_id == session.id,
            Participant.user_name == req.user_name,
        )
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found in session")

    restaurant = db.scalar(
        select(Restaurant).where(
            Restaurant.id == req.restaurant_id,
            Restaurant.session_id == session.id,
        )
    )
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found in session")

    existing_vote = db.scalar(
        select(Vote).where(
            Vote.session_id == session.id,
            Vote.participant_name == req.user_name,
            Vote.restaurant_id == req.restaurant_id,
        )
    )
    duplicate = False
    if existing_vote:
        if existing_vote.decision != req.decision:
            raise HTTPException(status_code=409, detail="Vote already exists with different decision")
        duplicate = True
    else:
        db.add(
            Vote(
                session_id=session.id,
                participant_name=req.user_name,
                restaurant_id=req.restaurant_id,
                decision=req.decision,
            )
        )
        db.flush()

    total_participants = db.scalar(
        select(func.count(Participant.id)).where(Participant.session_id == session.id)
    ) or 0
    votes_submitted_for_restaurant = db.scalar(
        select(func.count(Vote.id)).where(
            Vote.session_id == session.id,
            Vote.restaurant_id == req.restaurant_id,
        )
    ) or 0
    yes_votes_for_restaurant = db.scalar(
        select(func.count(Vote.id)).where(
            Vote.session_id == session.id,
            Vote.restaurant_id == req.restaurant_id,
            Vote.decision == "yes",
        )
    ) or 0

    matched = total_participants > 0 and yes_votes_for_restaurant == total_participants
    matched_restaurant_id = req.restaurant_id if matched else None

    next_restaurant = get_next_restaurant_for_user(db, session.id, req.user_name)

    next_yes_votes = 0
    next_total_votes = 0
    if next_restaurant:
        next_yes_votes = db.scalar(
            select(func.count(Vote.id)).where(
                Vote.session_id == session.id,
                Vote.restaurant_id == next_restaurant.id,
                Vote.decision == "yes",
            )
        ) or 0
        next_total_votes = db.scalar(
            select(func.count(Vote.id)).where(
                Vote.session_id == session.id,
                Vote.restaurant_id == next_restaurant.id,
            )
        ) or 0

    db.commit()

    await ws_manager.broadcast(
        room_code,
        {
            "event": "vote_progress",
            "restaurant_id": req.restaurant_id,
            "votes_submitted_for_restaurant": votes_submitted_for_restaurant,
            "yes_votes_for_restaurant": yes_votes_for_restaurant,
            "total_participants": total_participants,
        },
    )
    if matched:
        await ws_manager.broadcast(
            room_code,
            {
                "event": "match_found",
                "restaurant_id": req.restaurant_id,
                "restaurant_name": restaurant.name,
                "restaurant_image_url": restaurant.image_url,
                "total_participants": total_participants,
            },
        )

    return VoteResponse(
        duplicate=duplicate,
        matched=matched,
        matched_restaurant_id=matched_restaurant_id,
        total_participants=total_participants,
        votes_submitted_for_restaurant=votes_submitted_for_restaurant,
        yes_votes_for_restaurant=yes_votes_for_restaurant,
        next_restaurant=build_restaurant_card(next_restaurant) if next_restaurant else None,
        next_yes_votes=next_yes_votes,
        next_total_votes=next_total_votes,
    )


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


@app.get("/sessions/{room_code}/results", response_model=SessionResultsResponse)
def get_session_results(room_code: str, db: Session = Depends(get_db)):
    session = db.scalar(select(SessionModel).where(SessionModel.room_code == room_code))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    total_participants = (
        db.scalar(select(func.count(Participant.id)).where(Participant.session_id == session.id)) or 0
    )

    yes_votes = func.coalesce(
        func.sum(
            case(
                (Vote.decision == "yes", 1),
                else_=0,
            )
        ),
        0,
    ).label("yes_votes")
    total_votes = func.count(Vote.id).label("total_votes")

    ranking = db.execute(
        select(Restaurant, yes_votes, total_votes)
        .outerjoin(
            Vote,
            (Vote.restaurant_id == Restaurant.id) & (Vote.session_id == session.id),
        )
        .where(Restaurant.session_id == session.id)
        .group_by(Restaurant.id)
        .order_by(yes_votes.desc(), total_votes.desc(), Restaurant.id.asc())
    ).all()

    return SessionResultsResponse(
        total_participants=total_participants,
        results=[
            SessionResultItem(
                restaurant=build_restaurant_card(restaurant),
                yes_votes=int(yes_votes_count or 0),
                total_votes=int(total_votes_count or 0),
            )
            for restaurant, yes_votes_count, total_votes_count in ranking
        ],
    )


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
