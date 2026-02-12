from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
from app.models import Base, Participant, Restaurant, Session as SessionModel, Vote, YelpQueryCache


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


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db_sessionmaker():
    return TestingSessionLocal


@pytest.fixture(autouse=True)
def cleanup_db(db_sessionmaker) -> Generator[None, None, None]:
    db = db_sessionmaker()
    db.execute(delete(Vote))
    db.execute(delete(Restaurant))
    db.execute(delete(YelpQueryCache))
    db.execute(delete(Participant))
    db.execute(delete(SessionModel))
    db.commit()
    db.close()
    yield
