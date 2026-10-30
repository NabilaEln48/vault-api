def _upload(client, headers, name="hello.txt", content=b"hello vault"):
    return client.post(
        "/files",
        files={"file": (name, content, "text/plain")},
        headers=headers,
    )


def test_upload_and_download_roundtrip(client, auth_headers):
    upload = _upload(client, auth_headers)
    assert upload.status_code == 201
    body = upload.json()
    assert body["original_name"] == "hello.txt"
    assert body["size_bytes"] == len(b"hello vault")
    assert body["sha256"]
    download = client.get(f"/files/{body['id']}/download", headers=auth_headers)
    assert download.status_code == 200
    assert download.content == b"hello vault"


def test_upload_requires_unlocked_vault(client, auth_headers):
    client.post("/auth/lock", headers=auth_headers)
    response = _upload(client, auth_headers)
    assert response.status_code == 423
    client.post("/auth/unlock", json={"password": "secret123"}, headers=auth_headers)


def test_list_and_search_files(client, auth_headers):
    _upload(client, auth_headers, "report.pdf", b"pdf-bytes")
    _upload(client, auth_headers, "photo.png", b"png-bytes")
    response = client.get("/files", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2
    response = client.get("/files", params={"q": "photo"}, headers=auth_headers)
    assert [f["original_name"] for f in response.json()] == ["photo.png"]


def test_file_metadata_and_rename(client, auth_headers):
    file_id = _upload(client, auth_headers).json()["id"]
    meta = client.get(f"/files/{file_id}", headers=auth_headers)
    assert meta.status_code == 200
    assert meta.json()["original_name"] == "hello.txt"
    renamed = client.patch(
        f"/files/{file_id}",
        json={"original_name": "renamed.txt"},
        headers=auth_headers,
    )
    assert renamed.status_code == 200
    assert renamed.json()["original_name"] == "renamed.txt"


def test_other_user_cannot_access_file(client, auth_headers, second_auth_headers):
    file_id = _upload(client, auth_headers).json()["id"]
    assert client.get(f"/files/{file_id}", headers=second_auth_headers).status_code == 404
    assert (
        client.get(f"/files/{file_id}/download", headers=second_auth_headers).status_code
        == 404
    )


def test_delete_file(client, auth_headers):
    file_id = _upload(client, auth_headers).json()["id"]
    response = client.delete(f"/files/{file_id}", headers=auth_headers)
    assert response.status_code == 204
    assert client.get(f"/files/{file_id}", headers=auth_headers).status_code == 404
