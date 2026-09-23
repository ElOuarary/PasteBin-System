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

def test_create_wrong_accept():
    paste = generate_test_paste()
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/html",
        "Authorization": f"Bearer {token}"
    }
    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "application/json is only supported value for the Accept"}

def test_read():
    paste = generate_test_paste()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 201
    paste_id = response.json()["id"]
    response = client.get(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 200
    paste_read = response.json()
    assert "id" in paste_read[0] and paste_read[0]["id"] == paste_id
    assert "content" in paste_read[0]
    assert "username" in paste_read[0]
    assert "created_at" in paste_read[0]
    assert "expires_at" in paste_read[0]
    assert "view_count" in paste_read[0] and paste_read[0]["view_count"] == 1
    assert "is_private" in paste_read[0]
    assert "tags" in paste_read[0]
    response = client.get(f"/paste/{paste_id}", headers=headers)
    assert response.json()[0]["view_count"] == 2

def test_read_non_existent_paste():
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    paste_id = 999_999
    response = client.get(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "not found"}

def test_read_wrong_accept():
    paste = generate_test_paste()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 201
    
    headers["Accept"] = "text/html"
    paste_id = response.json()["id"]
    response = client.get(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "application/json is only supported value for the Accept"}
    