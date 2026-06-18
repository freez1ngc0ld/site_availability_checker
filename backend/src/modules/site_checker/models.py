from sqlalchemy import String, ForeignKey, Integer, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.base.model import Base

class SiteCheckerUserModel(Base):
    __tablename__ = 'site_checker_users'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    checker_id: Mapped[str] = mapped_column(ForeignKey('site_checkers.id', ondelete='CASCADE'), primary_key=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'checker_id', name='uq_user_checker'),
    )

class SiteCheckerModel(Base):
    __tablename__ = 'site_checkers'

    site_url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    checker_logs: Mapped[list["CheckerLogModel"]] = relationship(
        back_populates='checker', 
        cascade="all, delete-orphan"
    )

class CheckerLogModel(Base):
    __tablename__ = 'checker_logs'
    checker_id: Mapped[str] = mapped_column(ForeignKey('site_checkers.id', ondelete='CASCADE'), index=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    checker: Mapped["SiteCheckerModel"] = relationship(back_populates='checker_logs')
