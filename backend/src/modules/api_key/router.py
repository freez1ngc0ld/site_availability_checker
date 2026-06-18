from fastapi import APIRouter, status, Depends
from .dependencies import get_api_key_service
from .service import APIKeyService
from .schemas import APIKeySchema
from src.modules.auth.models import UserModel
from src.modules.auth.dependencies import get_current_user

router = APIRouter(prefix='/api_keys', tags=['API Keys'])

@router.get('', status_code=status.HTTP_200_OK, response_model=list[APIKeySchema])
async def all_api_keys(limit: str | None = None, offset: str | None = None, user: UserModel = Depends(get_current_user), api_key_service: APIKeyService = Depends(get_api_key_service)):
    return await api_key_service.get_user_api_keys(user_id=user.id, limit=limit, offset=offset)

@router.post('', status_code=status.HTTP_201_CREATED, response_model=APIKeySchema)
async def create_api_key(user: UserModel = Depends(get_current_user), api_key_service: APIKeyService = Depends(get_api_key_service)):   
    return await api_key_service.create_api_key(user_id=user.id)

@router.delete('/{api_key}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(api_key: str, user: UserModel = Depends(get_current_user), api_key_service: APIKeyService = Depends(get_api_key_service)) -> None:
    await api_key_service.delete_api_key(api_key=api_key, user_id=user.id)
