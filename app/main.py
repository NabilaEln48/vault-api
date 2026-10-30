import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.config import settings
from app.database import Base, engine
from app.routers import auth, files, folders, shares


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.VAULT_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="vault-api",
    description="Personal encrypted file vault API — project 4 of a 15-project backend series.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(folders.router)
app.include_router(files.router)
app.include_router(shares.router)


@app.get("/health", tags=["ops"])
def healthcheck() -> dict:
    return {"status": "ok"}
