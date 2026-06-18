from sqlalchemy.ext.asyncio import AsyncSession
from .repositories import APIKeyRepository
from .schemas import APIKeySchema
from .exceptions import *
from loguru import logger


class APIKeyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_repo = APIKeyRepository(self.db)

    async def get_user_api_keys(self, user_id: str, limit: str | None, offset: str | None) -> list[APIKeySchema]:
        api_keys = await self.api_repo.get_all(user_id=user_id, limit=limit, offset=offset)
        return [APIKeySchema.model_validate(api_key) for api_key in api_keys]

    async def create_api_key(self, user_id: str) -> APIKeySchema:
        api_key = await self.api_repo.create(user_id=user_id)
        await self.db.commit()
        logger.info("User {user_id} created API key {masked_key}", user_id=user_id, masked_key = f"{api_key.key[:16]}...{api_key.key[-4:]}")
        return APIKeySchema(key=api_key.key)

    async def delete_api_key(self, user_id: str, api_key: str) -> None:
        api_key = await self.api_repo.get_first(user_id=user_id, key=api_key)
        if not api_key:
            raise APIKeyNotFoundException()
        await self.api_repo.delete(api_key.id)
        await self.db.commit()
        logger.info("User {user_id} deleted API key {masked_key}", user_id=user_id, masked_key = f"{api_key.key[:16]}...{api_key.key[-4:]}")
        