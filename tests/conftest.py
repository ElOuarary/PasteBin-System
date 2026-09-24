import pytest
from fastapi.testclient import TestClient

from main import app
from utils.generate_paste import generate_test_paste
from utils.generate_user import generate_test_user


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def token(client):
    test_user = generate_test_user()
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    response = client.post("/auth/login", data=test_user)
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.fixture
def json_headers():
    return {"Content-Type": "application/json", "Accept": "application/json"}


@pytest.fixture
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def headers(json_headers, auth_headers):
    return json_headers | auth_headers

@pytest.fixture
def paste():
    return generate_test_paste()
