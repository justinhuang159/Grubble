from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
from app.models import Base, Participant, Restaurant, Session as SessionModel, YelpQueryCache


engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base.metadata.create_all(bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_db() -> Generator[None, None, None]:
    db = TestingSessionLocal()
    db.execute(delete(Restaurant))
    db.execute(delete(YelpQueryCache))
    db.execute(delete(Participant))
    db.execute(delete(SessionModel))
    db.commit()
    db.close()
    yield


def create_default_session() -> str:
    create_res = client.post(
        "/sessions",
        json={
            "host_name": "Justin",
            "cuisine": "sushi",
            "price": "1,2",
            "radius_meters": 3000,
            "location_text": "San Francisco, CA",
        },
    )
    assert create_res.status_code == 200
    return create_res.json()["room_code"]


def test_create_and_start_session_caches_restaurants(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    monkeypatch.setenv("RAPIDAPI_HOST", "example-host")

    from app import main as main_module

    def fake_search(
        self, *, term: str, location: str, price: str | None, radius_meters: int | None, limit: int = 30
    ):
        assert term == "sushi"
        assert location == "San Francisco, CA"
        assert price == "1,2"
        assert radius_meters == 3000
        return [
            {
                "id": "abc123",
                "name": "Sushi Place",
                "image_url": "https://img.example/sushi.jpg",
                "location": {"display_address": ["1 Main St", "San Francisco, CA"]},
                "coordinates": {"latitude": 37.78, "longitude": -122.41},
                "price": "$$",
                "rating": 4.5,
                "review_count": 220,
            }
        ]

    monkeypatch.setattr(main_module.YelpClient, "search_businesses", fake_search)

    room_code = create_default_session()
    start_res = client.post(f"/sessions/{room_code}/start", json={"host_name": "Justin"})
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "active"

    db = TestingSessionLocal()
    session = db.scalar(select(SessionModel).where(SessionModel.room_code == room_code))
    assert session is not None
    restaurants = db.scalars(select(Restaurant).where(Restaurant.session_id == session.id)).all()
    db.close()
    assert len(restaurants) == 1
    assert restaurants[0].name == "Sushi Place"


def test_start_session_fails_when_rapidapi_config_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.delenv("RAPIDAPI_HOST", raising=False)
    room_code = create_default_session()

    start_res = client.post(f"/sessions/{room_code}/start", json={"host_name": "Justin"})
    assert start_res.status_code == 500
    assert "RAPIDAPI_KEY" in start_res.json()["detail"]


def test_start_session_fails_when_no_restaurants_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    monkeypatch.setenv("RAPIDAPI_HOST", "example-host")

    from app import main as main_module

    def fake_empty(
        self, *, term: str, location: str, price: str | None, radius_meters: int | None, limit: int = 30
    ):
        return []

    monkeypatch.setattr(main_module.YelpClient, "search_businesses", fake_empty)

    room_code = create_default_session()
    start_res = client.post(f"/sessions/{room_code}/start", json={"host_name": "Justin"})
    assert start_res.status_code == 404
    assert "No restaurants found" in start_res.json()["detail"]


def test_start_session_rejects_non_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    monkeypatch.setenv("RAPIDAPI_HOST", "example-host")

    from app import main as main_module

    monkeypatch.setattr(main_module.YelpClient, "search_businesses", lambda self, **_: [])
    room_code = create_default_session()

    start_res = client.post(f"/sessions/{room_code}/start", json={"host_name": "Alex"})
    assert start_res.status_code == 403


def test_start_session_rejects_non_waiting_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    monkeypatch.setenv("RAPIDAPI_HOST", "example-host")

    from app import main as main_module

    monkeypatch.setattr(
        main_module.YelpClient,
        "search_businesses",
        lambda self, **_: [{"id": "abc123", "name": "Sushi Place"}],
    )
    room_code = create_default_session()

    first_start = client.post(f"/sessions/{room_code}/start", json={"host_name": "Justin"})
    assert first_start.status_code == 200

    second_start = client.post(f"/sessions/{room_code}/start", json={"host_name": "Justin"})
    assert second_start.status_code == 409


def test_start_session_uses_mock_data_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_MOCK_YELP", "true")
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.delenv("RAPIDAPI_HOST", raising=False)

    room_code = create_default_session()
    start_res = client.post(f"/sessions/{room_code}/start", json={"host_name": "Justin"})
    assert start_res.status_code == 200

    db = TestingSessionLocal()
    session = db.scalar(select(SessionModel).where(SessionModel.room_code == room_code))
    assert session is not None
    restaurants = db.scalars(select(Restaurant).where(Restaurant.session_id == session.id)).all()
    db.close()
    assert len(restaurants) >= 1
    assert restaurants[0].external_id.startswith("mock-")


def test_start_session_uses_query_cache_without_second_api_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("USE_MOCK_YELP", raising=False)
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    monkeypatch.setenv("RAPIDAPI_HOST", "example-host")
    monkeypatch.setenv("YELP_CACHE_TTL_MINUTES", "1440")

    from app import main as main_module

    call_count = {"count": 0}

    def fake_search(
        self, *, term: str, location: str, price: str | None, radius_meters: int | None, limit: int = 30
    ):
        call_count["count"] += 1
        return [{"id": "cache-1", "name": "Cached Place"}]

    monkeypatch.setattr(main_module.YelpClient, "search_businesses", fake_search)

    room_code_one = create_default_session()
    first_start = client.post(f"/sessions/{room_code_one}/start", json={"host_name": "Justin"})
    assert first_start.status_code == 200
    assert call_count["count"] == 1

    room_code_two = create_default_session()
    second_start = client.post(f"/sessions/{room_code_two}/start", json={"host_name": "Justin"})
    assert second_start.status_code == 200
    assert call_count["count"] == 1
