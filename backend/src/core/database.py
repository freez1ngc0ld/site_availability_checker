from src.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker[AsyncSession](bind=engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

