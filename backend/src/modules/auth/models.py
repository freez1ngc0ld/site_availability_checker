from src.core.base.model import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean


class UserModel(Base):
    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)

    hashed_password: Mapped[str] = mapped_column(String(64), nullable=True, default=None)
    google_id: Mapped[str] = mapped_column(String(512), unique=True, nullable=True, default=None)

    is_active: Mapped[bool] = mapped_column(Boolean(), default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean(), default=False)

