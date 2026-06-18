from src.core.base.repository import BaseRepository
from .models import UserModel


class UserRepository(BaseRepository):
    model = UserModel
