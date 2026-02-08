import asyncio
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.models import User

async def check_users():
    async with async_session_factory() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"Total users: {len(users)}")
        for u in users:
            print(f"User: {u.email}, ID: {u.id}, Active: {u.is_active}")

if __name__ == "__main__":
    asyncio.run(check_users())
