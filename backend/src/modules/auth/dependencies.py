from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from .exceptions import *
from src.core.security.token_manager import UserTokenManager
from src.core.security import token_types
from src.core.config import settings
from .repositories import UserRepository
from .service import AuthService
from src.core.database import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
token_manager = UserTokenManager(secret_key=settings.SECRET_KEY)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    payload = token_manager.verify_token(token)
    if not payload:
        raise InvalidTokenTypeException()
    
    user_id = payload.get("sub")
    token_type = payload.get("token_type") 

    if token_type != token_types.AUTHORIZATION:
        raise InvalidTokenTypeException()

    user_repository = UserRepository(db)
    user = await user_repository.get_by_pk(pk=user_id)

    if not user:
        raise UserNotFoundException()

    if not user.is_active:
        raise UserBannedException()

    if not user.is_verified:
        raise UserNotVerificatedException()
        
    return user


def get_auth_service(db: AsyncSession = Depends(get_db)):
    return AuthService(db)
