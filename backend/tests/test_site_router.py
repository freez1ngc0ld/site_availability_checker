import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from datetime import datetime, timedelta, timezone
from src.modules.site_checker.models import SiteCheckerModel, CheckerLogModel
from src.modules.auth.models import UserModel
from src.modules.site_checker.service import SiteService
from fastapi import status


@pytest.mark.asyncio
async def test_get_checkers_empty(client: AsyncClient, auth_headers):
    response = await client.get('/site_checkers', headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_add_checker_success(client: AsyncClient, auth_headers, get_db):
    target_url = 'https://www.youtube.com'

    response = await client.post('/site_checkers', params={'site_url': target_url}, headers=auth_headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['site_url'] == target_url
    assert 'id' in data

    result = await get_db.execute(select(SiteCheckerModel).where(SiteCheckerModel.site_url == target_url))
    checker = result.scalar_one_or_none()
    assert checker is not None


@pytest.mark.asyncio
async def test_get_checkers_pagination(client: AsyncClient, auth_headers, site_service: SiteService, verified_user: UserModel, get_db):
    c1 = await site_service.add_checker(user_id=verified_user.id, site_url='https://one.com')
    c2 = await site_service.add_checker(user_id=verified_user.id, site_url='https://two.com')
    c3 = await site_service.add_checker(user_id=verified_user.id, site_url='https://three.com')

    now = datetime.now(timezone.utc)
    await get_db.execute(update(SiteCheckerModel).where(SiteCheckerModel.id == c1.id).values(created_at=now - timedelta(seconds=2)))
    await get_db.execute(update(SiteCheckerModel).where(SiteCheckerModel.id == c2.id).values(created_at=now - timedelta(seconds=1)))
    await get_db.execute(update(SiteCheckerModel).where(SiteCheckerModel.id == c3.id).values(created_at=now))
    await get_db.commit()  

    response_limit = await client.get('/site_checkers', params={'limit': '2'}, headers=auth_headers)
    assert response_limit.status_code == status.HTTP_200_OK
    assert len(response_limit.json()) == 2

    response_offset = await client.get('/site_checkers', params={'limit': '2', 'offset': '2'}, headers=auth_headers)
    assert response_offset.status_code == status.HTTP_200_OK
    assert len(response_offset.json()) == 1
    assert response_offset.json()[0]['site_url'] == 'https://three.com'


@pytest.mark.asyncio
async def test_delete_checker_success(client: AsyncClient, auth_headers, site_service: SiteService, verified_user: UserModel, get_db):
    checker = await site_service.add_checker(user_id=verified_user.id, site_url='https://www.youtube.com')

    response = await client.delete(f'/site_checkers/{checker.id}', headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    result = await get_db.execute(select(SiteCheckerModel).where(SiteCheckerModel.id == checker.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_get_logs_last_24h(client: AsyncClient, auth_headers, site_service: SiteService, verified_user: UserModel):
    checker = await site_service.add_checker(user_id=verified_user.id, site_url='https://www.youtube.com')

    await site_service.log(checker_id=checker.id, status_code=status.HTTP_200_OK, response_time_ms=120)
    await site_service.log(checker_id=checker.id, status_code=status.HTTP_502_BAD_GATEWAY, response_time_ms=450)

    response = await client.get(f'/site_checkers/{checker.id}/logs', headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK

    logs = response.json()

    assert len(logs) == 2
    assert logs[0]['status_code'] == status.HTTP_200_OK
    assert logs[1]['status_code'] == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_add_checker_already_exists(client: AsyncClient, auth_headers, site_service: SiteService, verified_user: UserModel):
    url = 'https://www.youtube.com'

    await site_service.add_checker(user_id=verified_user.id, site_url=url)
    
    response = await client.post('/site_checkers', params={'site_url': url}, headers=auth_headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Site checker already exists'


@pytest.mark.asyncio
async def test_delete_checker_not_found(client: AsyncClient, auth_headers):
    fake_id = '12345-fake-id-67'
    response = await client.delete(f'/site_checkers/{fake_id}', headers=auth_headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Site checker not found'


@pytest.mark.asyncio
async def test_get_logs_of_unauthorized_checker(client: AsyncClient, auth_headers):
    invalid_checker_id = 'another-user-checker-id'
    response = await client.get(f'/site_checkers/{invalid_checker_id}/logs', headers=auth_headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Site checker not found'


@pytest.mark.asyncio
async def test_service_delete_old_logs(site_service: SiteService, verified_user: UserModel, get_db):
    checker = await site_service.add_checker(user_id=verified_user.id, site_url='https://www.youtube.com')

    await site_service.log(checker_id=checker.id, status_code=status.HTTP_200_OK, response_time_ms=100)

    old_log = await site_service.checker_log_repo.create(
        checker_id=checker.id,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        response_time_ms=999
    )
    old_log.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
    await get_db.commit()

    total_logs = await get_db.execute(select(CheckerLogModel).where(CheckerLogModel.checker_id == checker.id))
    assert len(total_logs.scalars().all()) == 2

    await site_service.delete_old_logs()

    remaining_logs = await get_db.execute(select(CheckerLogModel).where(CheckerLogModel.checker_id == checker.id))
    logs_left = remaining_logs.scalars().all()
    assert len(logs_left) == 1
    assert logs_left[0].status_code == status.HTTP_200_OK
