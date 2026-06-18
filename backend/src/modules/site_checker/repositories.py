from src.core.base.repository import BaseRepository
from .models import SiteCheckerModel, SiteCheckerUserModel, CheckerLogModel


class SiteCheckerRepository(BaseRepository):
    model = SiteCheckerModel


class SiteCheckerUserRepository(BaseRepository):
    model = SiteCheckerUserModel


class CheckerLogRepository(BaseRepository):
    model = CheckerLogModel


