"""Creates first admin user on startup if no users exist."""
import asyncio
from sqlalchemy import select
from app.core.config import AsyncSessionLocal, settings, engine
from app.core.auth import hash_password
from app.models import Base, User, UserRole


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if not settings.FIRST_ADMIN_EMAIL or not settings.FIRST_ADMIN_PASSWORD:
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            return
        admin = User(
            email=settings.FIRST_ADMIN_EMAIL,
            full_name="Admin",
            hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
            role=UserRole.admin,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print(f"[seed] Created admin: {settings.FIRST_ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(seed())
