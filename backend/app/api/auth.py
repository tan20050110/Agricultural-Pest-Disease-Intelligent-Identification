from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.auth_service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(request: RegisterRequest):
    result = register_user(
        username=request.username,
        email=request.email,
        password=request.password,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/login")
async def login(request: LoginRequest):
    result = login_user(
        username=request.username,
        password=request.password,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result