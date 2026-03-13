"""Authentication routes: register, login, profile."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext

from api.middleware.auth import create_token, require_auth
from api.schemas.auth import LoginRequest, RegisterRequest, StudentProfile, TokenResponse
from memory.store import MemoryStore

router = APIRouter(prefix="/auth", tags=["auth"])
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _get_store() -> MemoryStore:
    from api.app import get_memory_store
    return get_memory_store()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, store: MemoryStore = Depends(_get_store)) -> TokenResponse:
    existing = await store.get_student_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = _pwd.hash(req.password)
    student = await store.create_student(req.email, req.full_name, hashed)
    token = create_token(str(student.student_id))
    return TokenResponse(
        access_token=token,
        student_id=str(student.student_id),
        full_name=student.full_name,
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, store: MemoryStore = Depends(_get_store)) -> TokenResponse:
    student = await store.get_student_by_email(req.email)
    if not student or not _pwd.verify(req.password, student.hashed_pw):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(str(student.student_id))
    return TokenResponse(
        access_token=token,
        student_id=str(student.student_id),
        full_name=student.full_name,
    )


@router.get("/me", response_model=StudentProfile)
async def me(student_id: str = Depends(require_auth), store: MemoryStore = Depends(_get_store)) -> StudentProfile:
    student = await store.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentProfile(
        student_id=str(student.student_id),
        email=student.email,
        full_name=student.full_name,
        onboarded=student.onboarded,
        graduated=student.graduated,
    )
