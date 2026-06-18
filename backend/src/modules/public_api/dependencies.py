from fastapi import Depends
from fastapi.security import APIKeyQuery
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.api_key.exceptions import *
from src.modules.auth.exceptions import *
from src.core.database import get_db
from src.modules.auth.models import UserModel
from src.modules.api_key.repositories import APIKeyRepository

api_key_scheme = APIKeyQuery(name="api_key", auto_error=False)

async def get_user_by_api_key(
    api_key: str | None = Depends(api_key_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserModel:

    if not api_key:
        raise NoAPIKeyInQueryException()

    user = await APIKeyRepository(db).get_user_by_key(api_key)

    if not user:
        raise BadAPIKeyException()

    if not user.is_active:
        raise UserBannedException()

    if not user.is_verified:
        raise UserNotVerificatedException()
    
    return user
