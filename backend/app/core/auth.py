from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings, get_db
from app.models import User, UserRole

# Define Limiter here to avoid circular imports with routers
limiter = Limiter(key_func=get_remote_address)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLE_LEVEL = {
    UserRole.view_only:  1,
    UserRole.data_entry: 2,
    UserRole.admin:      3,
}

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(user_id: UUID, role: UserRole) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role.value, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not validate credentials or missing token")
    
    # SECURE: Read token from HttpOnly Cookie (Immune to XSS)
    token = request.cookies.get("access_token")
    
    # Fallback for Swagger UI testing (optional)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise exc

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise exc
    except JWTError:
        raise exc

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if user is None:
        raise exc
    return user

def require_role(minimum_role: UserRole):
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if ROLE_LEVEL[current_user.role] < ROLE_LEVEL[minimum_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Requires '{minimum_role.value}' role or higher")
        return current_user
    return _check