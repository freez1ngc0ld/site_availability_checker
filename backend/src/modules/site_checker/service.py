from sqlalchemy.ext.asyncio import AsyncSession
from .repositories import SiteCheckerRepository, SiteCheckerUserRepository, CheckerLogRepository 
from .exceptions import *
from .schemas import SiteCheckerSchema, CheckerLogSchema
from .models import SiteCheckerModel, CheckerLogModel
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from loguru import logger


class SiteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.site_checker_repo = SiteCheckerRepository(self.db)
        self.site_checker_user_repo = SiteCheckerUserRepository(self.db)
        self.checker_log_repo = CheckerLogRepository(self.db)

    async def get_user_checkers(self, user_id: str, limit: str | None, offset: str | None) -> list[SiteCheckerSchema]:
        user_links = await self.site_checker_user_repo.get_all(user_id=user_id)
        if not user_links:
            return []
        checker_ids = [link.checker_id for link in user_links]
        stmt = select(SiteCheckerModel).where(SiteCheckerModel.id.in_(checker_ids))
        stmt = stmt.order_by(SiteCheckerModel.created_at.asc(), SiteCheckerModel.id.asc())

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        checkers = result.scalars().all()
        return [SiteCheckerSchema.model_validate(checker) for checker in checkers]
        
    async def add_checker(self, user_id: str, site_url: str) -> SiteCheckerSchema:
        site_checker = await self.site_checker_repo.get_first(site_url=site_url)
        if not site_checker:
            site_checker = await self.site_checker_repo.create(site_url=site_url)
        link_exists = await self.site_checker_user_repo.get_first(
            user_id=user_id, 
            checker_id=site_checker.id
        )
        if link_exists:
            raise CheckerAlreadyExistsException()

        await self.site_checker_user_repo.create(user_id=user_id, checker_id=site_checker.id)
        await self.db.commit()

        logger.info('Created new site checker. ID: {checker_id}', checker_id=site_checker.id)

        return SiteCheckerSchema.model_validate(site_checker)
    
    async def delete_checker(self, user_id: str, checker_id: str) -> None:
        site_checker = await self.site_checker_user_repo.get_first(user_id=user_id, checker_id=checker_id)
        if not site_checker:
            raise CheckerNotFoundException()  
        await self.db.delete(site_checker)
        await self.db.flush()
        remaining_links = await self.site_checker_user_repo.get_all(checker_id=checker_id)
        if not remaining_links:
            await self.site_checker_repo.delete(checker_id)

        await self.db.commit()

        logger.info('Deleted site checker. ID: {checker_id}', checker_id=site_checker.id)
    
    async def log(self, checker_id: str, status_code: int, response_time_ms: int) -> CheckerLogSchema:
        log = await self.checker_log_repo.create(
            checker_id=checker_id,                 
            status_code=status_code, 
            response_time_ms=response_time_ms
        )
        await self.db.commit()
        return CheckerLogSchema.model_validate(log)
        
    async def get_all_last_24h_logs(self, user_id: str, checker_id: str) -> list[CheckerLogSchema]:
        link_exists = await self.site_checker_user_repo.get_first(user_id=user_id, checker_id=checker_id)
        if not link_exists:
            raise CheckerNotFoundException()
            
        now = datetime.now(timezone.utc)
        start_datetime = now - timedelta(hours=24)

        logs = await self.checker_log_repo.get_all(
            checker_id=checker_id, 
            between_field='created_at', 
            between_start=start_datetime, 
            between_end=now, 
            order_by='created_at' 
        )
        return [CheckerLogSchema.model_validate(log) for log in logs]
    
    async def delete_old_logs(self) -> None:
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(hours=24)
        stmt = delete(CheckerLogModel).where(CheckerLogModel.created_at < threshold)
        await self.db.execute(stmt)
        await self.db.commit()
