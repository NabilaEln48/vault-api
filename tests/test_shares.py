def _upload(client, headers):
    return client.post(
        "/files",
        files={"file": ("shared.txt", b"shared contents", "text/plain")},
        headers=headers,
    ).json()


def test_create_share_and_public_download(client, auth_headers):
    file_id = _upload(client, auth_headers)["id"]
    share = client.post(
        f"/files/{file_id}/shares",
        json={},
        headers=auth_headers,
    )
    assert share.status_code == 201
    token = share.json()["token"]
    assert share.json()["url"] == f"/shares/{token}"
    download = client.get(f"/shares/{token}")
    assert download.status_code == 200
    assert download.content == b"shared contents"


def test_share_requires_auth_to_create(client, auth_headers):
    file_id = _upload(client, auth_headers)["id"]
    assert client.post(f"/files/{file_id}/shares", json={}).status_code == 401


def test_expired_share_is_gone(client, auth_headers):
    file_id = _upload(client, auth_headers)["id"]
    share = client.post(
        f"/files/{file_id}/shares",
        json={"expires_in_minutes": -1},
        headers=auth_headers,
    )
    token = share.json()["token"]
    assert client.get(f"/shares/{token}").status_code == 410


def test_share_download_limit(client, auth_headers):
    file_id = _upload(client, auth_headers)["id"]
    share = client.post(
        f"/files/{file_id}/shares",
        json={"max_downloads": 1},
        headers=auth_headers,
    )
    token = share.json()["token"]
    assert client.get(f"/shares/{token}").status_code == 200
    assert client.get(f"/shares/{token}").status_code == 410


def test_revoke_share(client, auth_headers):
    file_id = _upload(client, auth_headers)["id"]
    share = client.post(
        f"/files/{file_id}/shares", json={}, headers=auth_headers
    ).json()
    response = client.delete(f"/shares/{share['id']}", headers=auth_headers)
    assert response.status_code == 204
    assert client.get(f"/shares/{share['token']}").status_code == 404


def test_share_lists_and_counts_downloads(client, auth_headers):
    file_id = _upload(client, auth_headers)["id"]
    share = client.post(
        f"/files/{file_id}/shares", json={}, headers=auth_headers
    ).json()
    client.get(f"/shares/{share['token']}")
    listed = client.get("/shares", headers=auth_headers).json()
    assert len(listed) == 1
    assert listed[0]["download_count"] == 1
