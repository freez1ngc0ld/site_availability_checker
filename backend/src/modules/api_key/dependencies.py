from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from .service import APIKeyService


def get_api_key_service(db: AsyncSession = Depends(get_db)):
    return APIKeyService(db)

