from fastapi.testclient import TestClient

from main import app
from utils.generate_user import generate_test_user, generate_username

client = TestClient(app)

def test_register():
    test_user = generate_test_user()
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    assert "id" in response.json() and "username" in response.json()
    assert response.json()["username"] == test_user["username"]

def test_register_duplicate_username_email():
    test_user = generate_test_user()

    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    assert "id" in response.json() and "username" in response.json()
    assert response.json()["username"] == test_user["username"]

    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 409
    assert response.json() == {"detail": "Username or email is already taken"}

    
def test_register_dupliacte_email():
    test_user = generate_test_user()
    
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    assert "id" in response.json() and "username" in response.json()
    assert response.json()["username"] == test_user["username"]

    test_user["username"] = generate_username()
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 409
    assert response.json() == {"detail": "Username or email is already taken"}
    