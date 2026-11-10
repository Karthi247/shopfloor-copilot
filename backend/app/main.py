from typing import Literal

import chromadb
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.config import settings
from app.services.answer_service import answer_question
from app.services.auth_service import (
    authenticate_user,
    change_password,
    issue_access_token,
    register_user,
    update_profile,
    verify_access_token,
)
from app.services.ingestion_service import ingest_documents
from app.services.revision_service import latest_revision

app = FastAPI(title="ShopFloor AI Copilot", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Admin-Token"],
)

bearer_scheme = HTTPBearer(auto_error=False)


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=10, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class ProfileRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=3, max_length=254)


class PasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=8)


def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Please log in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = verify_access_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Your session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@app.post("/api/auth/signup")
def signup(req: SignupRequest):
    try:
        user = register_user(req.name, req.email, req.password)
        return {
            "access_token": issue_access_token(user),
            "token_type": "bearer",
            "user": user,
        }
    except ValueError as exc:
        detail = str(exc)
        raise HTTPException(
            status_code=409 if "already exists" in detail else 400, detail=detail
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Email or password is incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return {
            "access_token": issue_access_token(user),
            "token_type": "bearer",
            "user": user,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/auth/me")
def get_profile(user: dict = Depends(require_user)):
    return user


@app.patch("/api/auth/me")
def patch_profile(req: ProfileRequest, user: dict = Depends(require_user)):
    try:
        updated = update_profile(user["id"], req.name, req.email)
    except ValueError as exc:
        detail = str(exc)
        raise HTTPException(
            status_code=409 if "already used" in detail else 400, detail=detail
        )
    if not updated:
        raise HTTPException(status_code=404, detail="Account not found.")
    return updated


@app.post("/api/auth/password")
def patch_password(req: PasswordRequest, user: dict = Depends(require_user)):
    try:
        change_password(user["id"], req.current_password, req.new_password)
    except ValueError as exc:
        detail = str(exc)
        raise HTTPException(
            status_code=400 if "Current password" in detail else 422, detail=detail
        )
    return {"status": "ok"}


@app.get("/api/health")
def health():
    try:
        count = (
            chromadb.PersistentClient(path=str(settings.chroma_path))
            .get_or_create_collection("shopfloor_documents")
            .count()
        )
    except Exception:
        count = 0
    return {"status": "ok", "indexed_chunks": count, "provider": settings.provider}


@app.get("/api/documents")
def documents(_user: dict = Depends(require_user)):
    try:
        c = chromadb.PersistentClient(
            path=str(settings.chroma_path)
        ).get_or_create_collection("shopfloor_documents")
        rows = c.get(include=["metadatas"])["metadatas"]
        seen = {}
        for m in rows:
            seen[(m["document_number"], m["revision"], m["filename"])] = m
        revisions = {}
        for m in rows:
            revisions.setdefault(m["document_number"], []).append(m)
        current = {
            number: latest_revision(group) for number, group in revisions.items()
        }
        return [
            {
                "document_number": m["document_number"],
                "revision": m["revision"] or None,
                "title": m["title"],
                "filename": m["filename"],
                "effective_date": m.get("effective_date"),
                "is_current": m["revision"] == current[m["document_number"]],
                "superseded_by": (
                    current[m["document_number"]]
                    if m["revision"] < current[m["document_number"]]
                    else None
                ),
            }
            for m in seen.values()
        ]
    except Exception:
        return []


@app.post("/api/chat")
def chat(req: ChatRequest, _user: dict = Depends(require_user)):
    try:
        return answer_question(
            req.question.strip(), [turn.model_dump() for turn in req.history]
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="The answer service is temporarily unavailable. Check backend configuration and logs.",
        )


@app.post("/api/admin/reindex")
def reindex(x_admin_token: str | None = Header(default=None)):
    if not settings.admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Valid X-Admin-Token is required.")
    try:
        return ingest_documents(force=True)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Document indexing failed. Check PDF files and backend logs.",
        )
