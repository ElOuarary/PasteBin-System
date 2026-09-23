from fastapi.testclient import TestClient

from main import app
from utils.generate_paste import generate_test_paste
from utils.generate_user import generate_test_user

client = TestClient(app)
token = None

test_user = generate_test_user()

try:
    client.post("/auth/register", json=test_user)
    response = client.post("/auth/login", data=test_user)
    token = response.json()["access_token"]
except Exception as e:
    raise e


def test_create():
    paste = generate_test_paste()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 201
    paste_read = response.json()
    assert "id" in paste_read
    assert "content" in paste_read
    assert "username" in paste_read
    assert "created_at" in paste_read
    assert "expires_at" in paste_read
    assert "view_count" in paste_read and paste_read["view_count"] == 0
    assert "is_private" in paste_read
    assert "tags" in paste_read

def test_create_wrong_content_type():
    paste = generate_test_paste()
    headers = {
        "Content-Type": "text/html",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 422
    assert response.json() == {"detail": "application/json is the only supported value for the Content-Type"}

def test_create_missing_accept():
    paste = generate_test_paste()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "application/json is only supported value for the Accept"}