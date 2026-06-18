from fastapi import APIRouter, status, Depends
from .dependencies import get_site_service
from .service import SiteService
from .schemas import SiteCheckerSchema, CheckerLogSchema
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import UserModel

router = APIRouter(prefix='/site_checkers', tags=['Site-checker endpoints'])

@router.get('', status_code=status.HTTP_200_OK, response_model=list[SiteCheckerSchema])
async def all_checkers(limit: str | None = None, offset: str | None = None, user: UserModel = Depends(get_current_user), site_service: SiteService = Depends(get_site_service)):
    return await site_service.get_user_checkers(user_id=user.id, limit=limit, offset=offset)

@router.post('', status_code=status.HTTP_201_CREATED, response_model=SiteCheckerSchema)
async def add_checker(site_url: str, user: UserModel = Depends(get_current_user), site_service: SiteService = Depends(get_site_service)):   
    return await site_service.add_checker(site_url=site_url, user_id=user.id)

@router.delete('/{checker_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_checker(checker_id: str, user: UserModel = Depends(get_current_user), site_service: SiteService = Depends(get_site_service)) -> None:
    await site_service.delete_checker(checker_id=checker_id, user_id=user.id)

@router.get('/{checker_id}/logs', status_code=status.HTTP_200_OK, response_model=list[CheckerLogSchema])
async def get_all_logs_today(checker_id: str, user: UserModel = Depends(get_current_user), site_service: SiteService = Depends(get_site_service)):
    return await site_service.get_all_last_24h_logs(user_id=user.id, checker_id=checker_id)
