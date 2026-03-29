"""认证路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .models import user_store
from .jwt_utils import create_token, hash_password, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class AuthRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(req: AuthRequest):
    if len(req.username) < 2 or len(req.password) < 4:
        raise HTTPException(400, "用户名至少2字符，密码至少4字符")
    existing = user_store.get_by_username(req.username)
    if existing:
        raise HTTPException(400, "用户名已存在")
    pw_hash = hash_password(req.password)
    user_id = user_store.create(req.username, pw_hash)
    token = create_token(user_id, req.username)
    return {"user_id": user_id, "username": req.username, "token": token}


@router.post("/login")
async def login(req: AuthRequest):
    user = user_store.get_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "用户名或密码错误")
    token = create_token(user["id"], user["username"])
    return {"user_id": user["id"], "username": user["username"], "token": token}
