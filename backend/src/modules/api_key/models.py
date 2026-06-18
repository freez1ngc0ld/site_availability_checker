from src.core.base.model import Base
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .utils import generate_new_api_key


class APIKeyModel(Base):
    __tablename__ = 'api_keys'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    key: Mapped[str] = mapped_column(String(128), default=generate_new_api_key, unique=True, index=True)
