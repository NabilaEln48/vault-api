def test_create_and_list_folders(client, auth_headers):
    response = client.post(
        "/folders", json={"name": "Documents"}, headers=auth_headers
    )
    assert response.status_code == 201
    folder_id = response.json()["id"]
    response = client.get("/folders", headers=auth_headers)
    assert response.status_code == 200
    assert [f["name"] for f in response.json()] == ["Documents"]
    response = client.get(f"/folders/{folder_id}", headers=auth_headers)
    assert response.json()["name"] == "Documents"


def test_nested_folder(client, auth_headers):
    parent = client.post(
        "/folders", json={"name": "Work"}, headers=auth_headers
    ).json()
    child = client.post(
        "/folders",
        json={"name": "Invoices", "parent_id": parent["id"]},
        headers=auth_headers,
    )
    assert child.status_code == 201
    assert child.json()["parent_id"] == parent["id"]


def test_folder_parent_must_exist(client, auth_headers):
    response = client.post(
        "/folders", json={"name": "Lost", "parent_id": 9999}, headers=auth_headers
    )
    assert response.status_code == 404


def test_rename_folder(client, auth_headers):
    folder = client.post(
        "/folders", json={"name": "Old"}, headers=auth_headers
    ).json()
    response = client.patch(
        f"/folders/{folder['id']}", json={"name": "New"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New"


def test_delete_folder_moves_files_to_root(client, auth_headers):
    folder = client.post(
        "/folders", json={"name": "Temp"}, headers=auth_headers
    ).json()
    upload = client.post(
        "/files",
        files={"file": ("a.txt", b"aaa", "text/plain")},
        data={"folder_id": folder["id"]},
        headers=auth_headers,
    )
    assert upload.status_code == 201
    file_id = upload.json()["id"]
    response = client.delete(f"/folders/{folder['id']}", headers=auth_headers)
    assert response.status_code == 204
    meta = client.get(f"/files/{file_id}", headers=auth_headers)
    assert meta.status_code == 200
    assert meta.json()["folder_id"] is None


def test_other_user_cannot_see_folder(client, auth_headers, second_auth_headers):
    folder = client.post(
        "/folders", json={"name": "Private"}, headers=auth_headers
    ).json()
    response = client.get(f"/folders/{folder['id']}", headers=second_auth_headers)
    assert response.status_code == 404
