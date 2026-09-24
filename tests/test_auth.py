import pytest

from utils.generate_user import (
    generate_email,
    generate_password,
    generate_test_user,
    generate_username,
)


def test_register(client):
    test_user = generate_test_user()
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert data["username"] == test_user["username"]


@pytest.mark.parametrize("duplicate", ["both", "username", "email"])
def test_register_duplicate_credentials(client, duplicate):
    test_user = generate_test_user()

    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert data["username"] == test_user["username"]
    if duplicate == "username":
        test_user["email"] = generate_email()
    elif duplicate == "email":
        test_user["username"] = generate_username()
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 409
    data = response.json()
    assert data == {"detail": "Username or email is already taken"}


def test_login(client):
    test_user = generate_test_user()
    user_creation = client.post("/auth/register", json=test_user)
    assert user_creation.status_code == 201

    response = client.post("/auth/login", data=test_user)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "Bearer"


@pytest.mark.parametrize("field", ["username", "password"])
def test_login_with_wrong_credentials(client, field):
    test_user = generate_test_user()
    user_creation = client.post("/auth/register", json=test_user)
    assert user_creation.status_code == 201

    if field == "username":
        test_user["username"] = generate_username()
    else:
        test_user["password"] = generate_password()

    response = client.post("/auth/login", data=test_user)
    assert response.status_code == 401

    headers = response.headers
    assert response.json() == {"detail": "Username or password is invalid"}
    assert "www-authenticate" in headers
    assert headers["www-authenticate"] == "Bearer"
