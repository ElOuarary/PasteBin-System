import pytest

from utils.generate_paste import generate_tags, generate_test_paste


def test_create(client, headers):
    paste = generate_test_paste()

    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "content" in data
    assert "username" in data
    assert "created_at" in data
    assert "expires_at" in data
    assert "view_count" in data
    assert data["view_count"] == 0
    assert "is_private" in data
    assert "tags" in data


def test_create_wrong_body_content(client, headers):
    paste = generate_test_paste(content_length=0)

    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 422
    assert "detail" in response.json()
    response = client.post("/paste", json={}, headers=headers)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_wrong_content_type(client, headers):
    paste = generate_test_paste()
    headers = headers | {"Content-Type": "text/html"}

    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 422
    assert response.json() == {
        "detail": "application/json is the only supported value for the Content-Type"
    }


def test_create_wrong_accept(client, headers):
    paste = generate_test_paste()
    headers = headers | {"Accept": "text/html"}
    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 400
    assert response.json() == {
        "detail": "application/json is only supported value for the Accept"
    }


def test_read(client, headers):
    paste = generate_test_paste()

    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 201

    paste_id = response.json()["id"]
    response = client.get(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "id" in data[0]
    assert data[0]["id"] == paste_id
    assert "content" in data[0]
    assert "username" in data[0]
    assert "created_at" in data[0]
    assert "expires_at" in data[0]
    assert "view_count" in data[0]
    assert data[0]["view_count"] == 1
    assert "is_private" in data[0]
    assert "tags" in data[0]

    response = client.get(f"/paste/{paste_id}", headers=headers)
    assert response.json()[0]["view_count"] == 2


def test_read_non_existent_paste(client, headers):
    paste_id = 999_999
    response = client.get(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "not found"}


def test_read_wrong_accept(client, headers):
    paste = generate_test_paste()

    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 201

    headers = headers | {"Accept": "text/html"}
    paste_id = response.json()["id"]
    response = client.get(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 400
    assert response.json() == {
        "detail": "application/json is only supported value for the Accept"
    }


def test_read_tags_filtered(client, headers):
    paste_1 = generate_test_paste()
    paste_2 = generate_test_paste()
    tags = generate_tags()
    paste_1["tags"] = paste_2["tags"] = tags

    response_1 = client.post("/paste", json=paste_1, headers=headers)
    response_2 = client.post("/paste", json=paste_2, headers=headers)
    assert response_1.status_code == 201
    assert response_2.status_code == 201

    search_tag = tags[0]
    response = client.get("/paste", params={"tag": search_tag}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    for paste in data:
        assert search_tag in paste["tags"]
        assert "view_count" in paste
        assert paste["view_count"] == 0


def test_read_non_existant_tags(client, headers):
    random_tag = generate_tags(count=1)

    response = client.get("/paste", params={"tag": random_tag}, headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "not found"}


@pytest.mark.parametrize("tags", ["normal", "empty", "null"])
def test_update(client, headers, tags):
    paste = generate_test_paste()
    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 201
    paste_id = response.json()["id"]
    response = client.get(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()[0]
    old_tags = data["tags"]

    if tags == "normal":
        new_tags = generate_tags()
        response = client.put(
            f"/paste/{paste_id}", json={"tags": new_tags}, headers=headers
        )
        assert response.status_code == 202
        data = response.json()

        assert "id" in data
        assert "content" in data
        assert "username" in data
        assert "created_at" in data
        assert "expires_at" in data
        assert "view_count" in data
        assert "is_private" in data
        assert "tags" in data
        assert new_tags == data["tags"]
        assert old_tags != new_tags
    elif tags == "empty":
        response = client.put(f"/paste/{paste_id}", json={"tags": []}, headers=headers)
        assert response.status_code == 202
        data = response.json()
        assert data["tags"] == []
    elif tags == "null":
        response = client.put(
            f"/paste/{paste_id}", json={"tags": None}, headers=headers
        )
        assert response.status_code == 202
        data = response.json()
        assert old_tags == data["tags"]


def test_delete(client, headers):
    paste = generate_test_paste()

    response = client.post("/paste", json=paste, headers=headers)
    assert response.status_code == 201

    paste_id = response.json()["id"]
    response = client.delete(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 204

    response = client.get(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 404

    response = client.delete(f"/paste/{paste_id}", headers=headers)
    assert response.status_code == 404
