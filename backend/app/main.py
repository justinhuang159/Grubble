import random
import string
from collections.abc import Generator
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import config  # noqa: F401
from .database import SessionLocal
from .integrations.yelp_client import MissingRapidAPIConfigError, YelpClient, YelpClientError
from .models import Participant, Restaurant, Session as SessionModel, YelpQueryCache
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
        db.add(
            Restaurant(
                session_id=session.id,
                external_id=external_id,
                name=str(item.get("name") or "Unknown Restaurant"),
                image_url=item.get("image_url"),
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
