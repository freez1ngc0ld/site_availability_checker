import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from src.main import app, api_app
from src.core.database import get_db as real_get_db_dependency
from src.core.base.model import Base
from src.modules.auth.models import UserModel
from src.modules.auth.service import AuthService
from src.modules.site_checker.service import SiteService
from src.modules.api_key.service import APIKeyService
from src.modules.auth.email import email_service
from src.core.security import token_types
from loguru import logger


engine = create_async_engine(
    'sqlite+aiosqlite:///:memory:',
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)
AsyncSessionLocal = async_sessionmaker[AsyncSession](bind=engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def get_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
            
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def disable_logging_during_tests():
    logger.add(lambda msg: None, level="CRITICAL")
    logger.disable("src")
    yield
    logger.enable("src")


@pytest.fixture
def auth_service(get_db):
    return AuthService(db=get_db)


@pytest.fixture
def site_service(get_db):
    return SiteService(db=get_db)


@pytest.fixture
def api_key_service(get_db):
    return APIKeyService(db=get_db)


@pytest.fixture
def mock_bg_tasks():
    return MagicMock()


@pytest.fixture
async def verified_user(auth_service: AuthService) -> UserModel:
    user = await auth_service.user_repo.create(
        email='bigjeff@island.us',
        hashed_password=auth_service.hash_password('12345678'),
        is_verified=True,
        is_active=True
    )
    await auth_service.db.commit()
    return user


@pytest.fixture(autouse=True)
def mock_email_notifications():
    email_service.send_token_email = AsyncMock(return_value=None)
    email_service.send_code_email = AsyncMock(return_value=None)
    yield email_service


@pytest_asyncio.fixture
async def client(get_db):
    async def _override_get_db():
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[real_get_db_dependency] = _override_get_db

    api_app.dependency_overrides[real_get_db_dependency] = _override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    api_app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(auth_service: AuthService, verified_user):
    token = auth_service.generate_token(user_id=verified_user.id, token_type=token_types.AUTHORIZATION)
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
async def public_api_key(api_key_service: APIKeyService, verified_user: UserModel) -> str:
    api_key_schema = await api_key_service.create_api_key(user_id=verified_user.id)
    return api_key_schema.key
