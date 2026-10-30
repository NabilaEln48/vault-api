def test_register_and_login(client):
    response = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "secret123"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "new@example.com"
    response = client.post(
        "/auth/login",
        data={"username": "new@example.com", "password": "secret123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_register_duplicate_email(client, auth_headers):
    response = client.post(
        "/auth/register",
        json={"email": "tester@example.com", "password": "secret123"},
    )
    assert response.status_code == 400


def test_login_wrong_password(client, auth_headers):
    response = client.post(
        "/auth/login",
        data={"username": "tester@example.com", "password": "nope-nope-nope"},
    )
    assert response.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "tester@example.com"


def test_change_password_keeps_vault_working(client, auth_headers):
    upload = client.post(
        "/files",
        files={"file": ("secret.txt", b"do not lose this", "text/plain")},
        headers=auth_headers,
    )
    assert upload.status_code == 201
    file_id = upload.json()["id"]
    response = client.post(
        "/auth/change-password",
        json={"current_password": "secret123", "new_password": "newsecret1"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    old_login = client.post(
        "/auth/login",
        data={"username": "tester@example.com", "password": "secret123"},
    )
    assert old_login.status_code == 401
    new_login = client.post(
        "/auth/login",
        data={"username": "tester@example.com", "password": "newsecret1"},
    )
    assert new_login.status_code == 200
    headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}
    client.post("/auth/unlock", json={"password": "newsecret1"}, headers=headers)
    download = client.get(f"/files/{file_id}/download", headers=headers)
    assert download.status_code == 200
    assert download.content == b"do not lose this"


def test_locked_vault_blocks_download(client, auth_headers):
    upload = client.post(
        "/files",
        files={"file": ("secret.txt", b"locked away", "text/plain")},
        headers=auth_headers,
    )
    file_id = upload.json()["id"]
    locked = client.post("/auth/lock", headers=auth_headers)
    assert locked.status_code == 200
    assert locked.json()["status"] == "locked"
    response = client.get(f"/files/{file_id}/download", headers=auth_headers)
    assert response.status_code == 423
    unlocked = client.post(
        "/auth/unlock", json={"password": "secret123"}, headers=auth_headers
    )
    assert unlocked.json()["status"] == "unlocked"
    response = client.get(f"/files/{file_id}/download", headers=auth_headers)
    assert response.status_code == 200
