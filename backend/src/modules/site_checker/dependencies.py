from .service import SiteService
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db


def get_site_service(db: AsyncSession = Depends(get_db)):
    return SiteService(db)
