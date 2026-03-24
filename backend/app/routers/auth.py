from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_db, settings
from app.core.auth import verify_password, create_access_token, get_current_user, limiter
from app.models import User

router = APIRouter()

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

@router.post("/login")
@limiter.limit("5/minute") # SECURE: Stops bots from brute-forcing passwords
async def login(
    request: Request,
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == form.username, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    token = create_access_token(user.id, user.role)
    
    # SECURE: Injecting the token as an HttpOnly Cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,  # Javascript cannot read this (Immune to XSS)
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax", # Protects against Cross-Site Request Forgery (CSRF)
        secure=False,   # Note: Set this to True when you move to HTTPS in production
    )

    return {
        "message": "Successfully logged in",
        "role": user.role.value,
        "full_name": user.full_name
    }

@router.post("/logout")
async def logout(response: Response):
    # Overwrite the cookie to instantly destroy the session
    response.delete_cookie("access_token", httponly=True, samesite="lax")
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
    )