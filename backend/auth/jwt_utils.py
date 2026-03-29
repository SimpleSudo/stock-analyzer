"""JWT 工具函数"""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("JWT_SECRET", "stock-analyzer-dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 72

security = HTTPBearer(auto_error=False)


def create_token(user_id: str, username: str) -> str:
    try:
        from jose import jwt
    except ImportError:
        # 降级：无 python-jose 时返回简单 token
        import hashlib
        return hashlib.sha256(f"{user_id}:{username}:{SECRET_KEY}".encode()).hexdigest()

    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": user_id, "username": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        from jose import jwt, JWTError
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ImportError:
        return None
    except Exception:
        return None


def hash_password(password: str) -> str:
    try:
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return ctx.hash(password)
    except ImportError:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return ctx.verify(plain, hashed)
    except ImportError:
        import hashlib
        return hashlib.sha256(plain.encode()).hexdigest() == hashed


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """可选认证：未登录返回 None，已登录返回用户信息"""
    if credentials is None:
        return None
    payload = verify_token(credentials.credentials)
    if payload is None:
        return None
    return payload


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """强制认证：未登录返回 401"""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 无效或已过期")
    return payload
