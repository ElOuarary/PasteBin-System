from utils.generate_paste import generate_test_paste, generate_tags
from utils.generate_user import generate_test_user

token = None

test_user = generate_test_user()

# There is a testing error that I need to solve due to httpx only handle http urls not
# endpoints
"""try:
    httpx.post("/auth/register", json=test_user)
    response = httpx.post("/auth/login", data=test_user)
    token = response.json()["access_token"]
except Exception as e:
    raise e"""


def test_create(client):
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

def test_create_wrong_body_content(client):
    paste = generate_test_paste(content_length=0)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 422
    assert "detail" in response.json()
    response = client.post("/paste", json={}, headers=headers)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_wrong_content_type(client):
    paste = generate_test_paste()
    headers = {
        "Content-Type": "text/html",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 422
    assert response.json() == {"detail": "application/json is the only supported value for the Content-Type"}

def test_create_wrong_accept(client):
    paste = generate_test_paste()
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/html",
        "Authorization": f"Bearer {token}"
    }
    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "application/json is only supported value for the Accept"}

def test_read(client):
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

def test_read_non_existent_paste(client):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    paste_id = 999_999
    response = client.get(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "not found"}

def test_read_wrong_accept(client):
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

def test_read_tags_filtered(client):
    paste_1 = generate_test_paste()
    paste_2 = generate_test_paste()
    tags = generate_tags()
    paste_1["tags"] = paste_2["tags"] = tags
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response_1 = client.post("/paste", json=paste_1, headers=headers)
    response_2 = client.post("/paste", json=paste_2, headers=headers)
    assert response_1.status_code == 201
    assert response_2.status_code == 201

    search_tag = tags[0]
    response = client.get("/paste", params={"tag": search_tag}, headers=headers)
    assert response.status_code == 200
    paste_read = response.json()
    for paste in paste_read:
        assert search_tag in paste["tags"]
        assert "view_count" in paste and paste["view_count"] == 0

def test_read_non_existant_tags(client):
    random_tag = generate_tags(count=1)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = client.get("/paste", params={"tag": random_tag}, headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "not found"}


def test_update(client):
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
    paste_read = response.json()[0] 
    old_tags = paste_read["tags"]
    new_tags = generate_tags()
    response = client.put(f"/paste/{paste_id}", json={"tags": new_tags},headers=headers)
    assert response.status_code == 202
    paste_read = response.json()
    assert "id" in paste_read
    assert "content" in paste_read
    assert "username" in paste_read
    assert "created_at" in paste_read
    assert "expires_at" in paste_read
    assert "view_count" in paste_read
    assert "is_private" in paste_read
    assert "tags" in paste_read and new_tags == paste_read["tags"] and old_tags != new_tags

def test_update_null_tags(client):
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

    paste_read = response.json()[0]
    old_tags = paste_read["tags"]

    response = client.put(f"/paste/{paste_id}", json={"tags": None}, headers=headers)
    assert response.status_code == 202
    paste_read = response.json()
    assert old_tags == paste_read["tags"]

def test_update_empty_tags(client):
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

    response = client.put(f"/paste/{paste_id}", json={"tags": []}, headers=headers)
    assert response.status_code == 202
    paste_read = response.json()
    assert paste_read["tags"] == []

def test_delete(client):
    paste = generate_test_paste()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 201

    paste_id = response.json()["id"]
    response = client.delete(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 204

    response = client.get(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 404

    response = client.delete(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 404