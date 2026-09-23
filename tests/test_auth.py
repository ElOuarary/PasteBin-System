from fastapi.testclient import TestClient

from main import app
from utils.generate_user import generate_test_user, generate_username, generate_password

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


def test_login():
    test_user = generate_test_user()
    user_creation = client.post("/auth/register", json=test_user)
    assert user_creation.status_code == 201
    response = client.post("/auth/login", data=test_user)
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert "token_type" in response.json() and response.json()["token_type"] == "Bearer"

def test_login_with_wrong_username():
    test_user = generate_test_user()
    user_creation = client.post("/auth/register", json=test_user)
    assert user_creation.status_code == 201

    test_user["username"] = generate_username()
    response = client.post("/auth/login", data=test_user)
    assert response.status_code == 401
    assert response.json() == {"detail": "Username or password is invalid"}
    assert "WWW-Authenticate".lower() in response.headers.keys() and response.headers["WWW-Authenticate"] == "Bearer"

def test_login_with_wrong_password():
    test_user = generate_test_user()
    user_creation = client.post("/auth/register", json=test_user)
    assert user_creation.status_code == 201

    test_user["password"] = generate_password()
    response = client.post("/auth/login", data=test_user)
    assert response.status_code == 401
    assert response.json() == {"detail": "Username or password is invalid"}
    assert "WWW-Authenticate".lower() in response.headers.keys() and response.headers["WWW-Authenticate"] == "Bearer"
    