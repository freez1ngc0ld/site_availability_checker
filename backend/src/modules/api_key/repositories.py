from src.core.base.repository import BaseRepository
from .models import APIKeyModel
from src.modules.auth.models import UserModel
from sqlalchemy import select


class APIKeyRepository(BaseRepository):
    model = APIKeyModel

    async def get_user_by_key(self, key: str) -> UserModel | None:
        query = (
            select(UserModel)
            .join(APIKeyModel, APIKeyModel.user_id == UserModel.id)
            .where(APIKeyModel.key == key)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
