# vault-api

Personal encrypted file vault API — project 4 of a 15-project backend series.

Upload files and they are encrypted before they ever touch the disk. Each
account has its own vault key, each file has its own data key, and share
links let other people download a file without ever seeing your vault.

Built with FastAPI, SQLAlchemy and SQLite. JWT auth with bcrypt passwords.

## How the encryption works

- Every account gets a random vault key at registration. The vault key is
  wrapped (encrypted) with a key derived from the account password using
  PBKDF2-HMAC-SHA256 with a per-user salt, so the server never stores a
  password or a vault key in plain text.
- Every file gets its own random data key (envelope encryption). The file
  bytes are encrypted with the data key using Fernet (AES-128-CBC with
  HMAC), and the data key is stored wrapped with the vault key.
- Changing your password re-wraps the vault key — files are never
  re-encrypted.
- A share link stores the file's data key wrapped with a key derived from
  the link token, so a shared file can be downloaded without unlocking the
  vault. Share links support expiry times and download limits.

## Vault lock

The vault starts locked. File uploads and downloads need the vault
unlocked: log in, then `POST /auth/unlock` with your password. The unlock
lasts 30 minutes, then the vault locks itself again. `POST /auth/lock`
locks it immediately. Listing file metadata works while locked, but no
file bytes move until you unlock.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Copy `.env` from the defaults in `app/config.py` to override
`DATABASE_URL`, `SECRET_KEY`, `VAULT_DIR` or `MAX_UPLOAD_SIZE_MB`.

Seed a demo account (`demo@vault.dev` / `demo1234`) with two folders and
two files:

```bash
python scripts/seed.py
```

## Endpoints

| Method | Path | What it does |
| --- | --- | --- |
| POST | /auth/register | Create an account and a vault key |
| POST | /auth/login | Log in, returns a JWT |
| GET | /auth/me | Current account |
| POST | /auth/change-password | Change password, re-wrap vault key |
| POST | /auth/unlock | Unlock the vault with your password |
| POST | /auth/lock | Lock the vault |
| POST | /folders | Create a folder |
| GET | /folders | List your folders |
| GET | /folders/{id} | Get one folder |
| PATCH | /folders/{id} | Rename or move a folder |
| DELETE | /folders/{id} | Delete a folder, files move to root |
| POST | /files | Upload a file, encrypted at rest |
| GET | /files | List and search files (`?q=`, `?folder_id=`) |
| GET | /files/{id} | File metadata |
| GET | /files/{id}/download | Download and decrypt a file |
| PATCH | /files/{id} | Rename or move a file |
| DELETE | /files/{id} | Delete a file and its stored bytes |
| POST | /files/{id}/shares | Create a share link |
| GET | /shares | List your share links |
| DELETE | /shares/{id} | Revoke a share link |
| GET | /shares/{token} | Download a shared file, no login needed |
| GET | /health | Health check |

## Tests

```bash
python -m pytest -q
```
