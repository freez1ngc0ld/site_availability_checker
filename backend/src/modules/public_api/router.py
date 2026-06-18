from fastapi import APIRouter, status, Depends
from .dependencies import get_user_by_api_key
from src.modules.site_checker.dependencies import get_site_service
from src.modules.site_checker.schemas import SiteCheckerSchema, CheckerLogSchema
from src.modules.site_checker.service import SiteService
from src.modules.auth.models import UserModel


router = APIRouter(tags=['Public API'])

@router.get('/checkers', status_code=status.HTTP_200_OK, response_model=list[SiteCheckerSchema])
async def all_checkers(limit: str | None = None, offset: str | None = None, user: UserModel = Depends(get_user_by_api_key), site_service: SiteService = Depends(get_site_service)):
    return await site_service.get_user_checkers(user_id=user.id, limit=limit, offset=offset)

@router.get('/checker_logs/{checker_id}', status_code=status.HTTP_200_OK, response_model=list[CheckerLogSchema])
async def get_all_logs_today(checker_id: str, user: UserModel = Depends(get_user_by_api_key), site_service: SiteService = Depends(get_site_service)):
    return await site_service.get_all_last_24h_logs(user_id=user.id, checker_id=checker_id)
