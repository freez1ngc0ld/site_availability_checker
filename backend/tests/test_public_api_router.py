import pytest
from httpx import AsyncClient
from sqlalchemy import update
from datetime import datetime, timedelta, timezone
from fastapi import status
from src.modules.site_checker.models import SiteCheckerModel
from src.modules.auth.models import UserModel
from src.modules.auth.service import AuthService
from src.modules.api_key.service import APIKeyService
from src.modules.site_checker.service import SiteService


@pytest.mark.asyncio
async def test_public_get_checkers_success(client: AsyncClient, public_api_key, site_service: SiteService, verified_user: UserModel):
    await site_service.add_checker(user_id=verified_user.id, site_url='https://www.youtube.com')

    response = await client.get('/api/checkers', params={'api_key': public_api_key})
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]['site_url'] == 'https://www.youtube.com'


@pytest.mark.asyncio
async def test_public_get_checkers_pagination(client: AsyncClient, public_api_key, site_service: SiteService, verified_user: UserModel, get_db):
    c1 = await site_service.add_checker(user_id=verified_user.id, site_url='https://one.com')
    c2 = await site_service.add_checker(user_id=verified_user.id, site_url='https://two.com')

    now = datetime.now(timezone.utc)
    await get_db.execute(update(SiteCheckerModel).where(SiteCheckerModel.id == c1.id).values(created_at=now - timedelta(seconds=5)))
    await get_db.execute(update(SiteCheckerModel).where(SiteCheckerModel.id == c2.id).values(created_at=now))
    await get_db.commit()

    response = await client.get('/api/checkers', params={'api_key': public_api_key, 'limit': '1', 'offset': '1'})
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]['site_url'] == 'https://two.com'


@pytest.mark.asyncio
async def test_public_get_logs_success(client: AsyncClient, public_api_key, site_service: SiteService, verified_user: UserModel):
    checker = await site_service.add_checker(user_id=verified_user.id, site_url='https://www.youtube.com')
    await site_service.log(checker_id=checker.id, status_code=status.HTTP_200_OK, response_time_ms=85)

    response = await client.get(f'/api/checker_logs/{checker.id}', params={'api_key': public_api_key})
    
    assert response.status_code == status.HTTP_200_OK
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]['status_code'] == status.HTTP_200_OK
    assert logs[0]['response_time_ms'] == 85


@pytest.mark.asyncio
async def test_public_missing_api_key(client: AsyncClient):
    response = await client.get('/api/checkers')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_public_bad_api_key(client: AsyncClient):
    response = await client.get('/api/checkers', params={'api_key': 'fake_key_value_unexistent'})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_public_banned_user(client: AsyncClient, api_key_service: APIKeyService, auth_service: AuthService):
    banned_user = await auth_service.user_repo.create(
        email='bannedbigjeff@island.us',
        hashed_password=auth_service.hash_password('12345678'),
        is_verified=True,
        is_active=False
    )
    await auth_service.db.commit()
    
    key_schema = await api_key_service.create_api_key(user_id=banned_user.id)

    response = await client.get('/api/checkers', params={'api_key': key_schema.key})

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_public_unverified_user(client: AsyncClient, api_key_service: APIKeyService, auth_service: AuthService):
    unverified_user = await auth_service.user_repo.create(
        email='unverifiedbigjeff@island.us',
        hashed_password=auth_service.hash_password('12345678'),
        is_verified=False,
        is_active=True
    )
    await auth_service.db.commit()
    
    key_schema = await api_key_service.create_api_key(user_id=unverified_user.id)

    response = await client.get('/api/checkers', params={'api_key': key_schema.key})

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_public_get_logs_share_violation(client: AsyncClient, public_api_key, auth_service: AuthService, site_service: SiteService):
    other_user = await auth_service.user_repo.create(
        email='otherbigjeff@island.us',
        hashed_password=auth_service.hash_password('12345678'),
        is_verified=True,
        is_active=True
    )
    await auth_service.db.commit()
    other_checker = await site_service.add_checker(user_id=other_user.id, site_url='https://www.youtube.com')

    response = await client.get(f'/api/checker_logs/{other_checker.id}', params={'api_key': public_api_key})

    assert response.status_code == status.HTTP_404_NOT_FOUND
