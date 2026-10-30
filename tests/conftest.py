import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite://"


@pytest.fixture()
def db_session():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login(client, email):
    client.post(
        "/auth/register",
        json={"email": email, "password": "secret123"},
    )
    response = client.post(
        "/auth/login",
        data={"username": email, "password": "secret123"},
    )
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    client.post("/auth/unlock", json={"password": "secret123"}, headers=headers)
    return headers


@pytest.fixture()
def auth_headers(client):
    return _login(client, "tester@example.com")


@pytest.fixture()
def second_auth_headers(client):
    return _login(client, "other@example.com")
