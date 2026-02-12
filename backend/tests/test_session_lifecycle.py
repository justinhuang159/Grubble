from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
from app.models import Base


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


def test_create_and_start_session_happy_path() -> None:
    create_res = client.post("/sessions", json={"host_name": "Justin"})
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["status"] == "waiting"

    room_code = created["room_code"]
    start_res = client.post(f"/sessions/{room_code}/start", json={"host_name": "Justin"})
    assert start_res.status_code == 200

    started = start_res.json()
    assert started["status"] == "active"
    assert started["host_name"] == "Justin"


def test_start_session_rejects_non_host() -> None:
    create_res = client.post("/sessions", json={"host_name": "Justin"})
    room_code = create_res.json()["room_code"]

    start_res = client.post(f"/sessions/{room_code}/start", json={"host_name": "Alex"})
    assert start_res.status_code == 403


def test_start_session_rejects_non_waiting_state() -> None:
    create_res = client.post("/sessions", json={"host_name": "Justin"})
    room_code = create_res.json()["room_code"]

    first_start = client.post(f"/sessions/{room_code}/start", json={"host_name": "Justin"})
    assert first_start.status_code == 200

    second_start = client.post(f"/sessions/{room_code}/start", json={"host_name": "Justin"})
    assert second_start.status_code == 409
