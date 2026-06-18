import pytest
from src.modules.site_checker.service import SiteService
from src.modules.site_checker.exceptions import *
from sqlalchemy import update, select
from src.modules.site_checker.models import SiteCheckerModel, CheckerLogModel
from datetime import datetime, timedelta, timezone
from src.modules.auth.models import UserModel


@pytest.mark.asyncio
async def test_create_site_checker(site_service: SiteService, verified_user: UserModel):
    site_url = 'https://www.youtube.com'

    checker = await site_service.add_checker(user_id=verified_user.id, site_url=site_url)

    checker_from_db = await site_service.site_checker_repo.get_first(site_url=site_url)
    assert checker_from_db.site_url == checker.site_url == site_url

    checker_user_from_db = await site_service.site_checker_user_repo.get_first(user_id=verified_user.id, checker_id=checker_from_db.id)
    assert checker_user_from_db.user_id == verified_user.id


@pytest.mark.asyncio
async def test_get_site_checkers(site_service: SiteService, verified_user: UserModel):
    site_url = 'https://www.youtube.com'

    checker = await site_service.add_checker(user_id=verified_user.id, site_url=site_url)

    checkers = await site_service.get_user_checkers(user_id=verified_user.id, limit=None, offset=None)
    assert checkers == [checker]


@pytest.mark.asyncio
async def test_get_site_checkers_limit_offset(site_service: SiteService, verified_user: UserModel):
    site_urls = [
        'https://www.youtube.com',
        'https://google.com',
        'https://grok.com',
        'https://steamcommunity.com',
        'https://github.com',
    ]

    for site_url in site_urls:
        await site_service.add_checker(user_id=verified_user.id, site_url=site_url)

    for i, site_url in enumerate(site_urls):
        await site_service.db.execute(
            update(SiteCheckerModel)
            .where(SiteCheckerModel.site_url == site_url)
            .values(created_at=datetime.now(timezone.utc) + timedelta(seconds=i))
        )
    await site_service.db.commit()

    all_checkers = await site_service.get_user_checkers(user_id=verified_user.id, limit=None, offset=None)

    checkers_l3o0 = await site_service.get_user_checkers(user_id=verified_user.id, limit=3, offset=0)
    assert checkers_l3o0 == all_checkers[0:3]

    checkers_l3o1 = await site_service.get_user_checkers(user_id=verified_user.id, limit=3, offset=1)
    assert checkers_l3o1 == all_checkers[1:4]

    checkers_lno3 = await site_service.get_user_checkers(user_id=verified_user.id, limit=None, offset=3)
    assert checkers_lno3 == all_checkers[3:5]


@pytest.mark.asyncio
async def test_delete_site_checker(site_service: SiteService, verified_user: UserModel):
    site_url = 'https://www.youtube.com'

    await site_service.add_checker(user_id=verified_user.id, site_url=site_url)

    checker_from_db = await site_service.site_checker_repo.get_first(site_url=site_url)
    assert checker_from_db is not None

    await site_service.delete_checker(user_id=verified_user.id, checker_id=checker_from_db.id)

    checker_from_db = await site_service.site_checker_repo.get_first(site_url=site_url)
    assert checker_from_db is None


@pytest.mark.asyncio
async def test_log(site_service: SiteService, verified_user: UserModel):
    site_url = 'https://www.youtube.com'

    checker = await site_service.add_checker(user_id=verified_user.id, site_url=site_url)

    log_schema = await site_service.log(checker_id=checker.id, status_code=200, response_time_ms=150)
    log = (await site_service.checker_log_repo.get_all())[-1]

    assert log_schema.status_code == 200
    assert log_schema.response_time_ms == 150
    assert log.checker_id == checker.id

    logs_from_db = await site_service.checker_log_repo.get_all(checker_id=checker.id)
    assert len(logs_from_db) == 1
    assert logs_from_db[0].status_code == 200
    assert logs_from_db[0].response_time_ms == 150


@pytest.mark.asyncio
async def test_get_all_last_24h_logs(site_service: SiteService, verified_user: UserModel):
    site_url = 'https://www.youtube.com'

    checker = await site_service.add_checker(user_id=verified_user.id, site_url=site_url)

    log_recent = await site_service.log(checker_id=checker.id, status_code=200, response_time_ms=100)
    log_old = await site_service.log(checker_id=checker.id, status_code=500, response_time_ms=999)

    old_time = datetime.now(timezone.utc) - timedelta(hours=25)
    await site_service.db.execute(
        update(CheckerLogModel)
        .where(CheckerLogModel.id == log_old.id)
        .values(created_at=old_time)
    )
    await site_service.db.commit()

    recent_logs = await site_service.get_all_last_24h_logs(user_id=verified_user.id, checker_id=checker.id)
    
    assert len(recent_logs) == 1
    assert recent_logs[0].id == log_recent.id
    assert recent_logs[0].status_code == 200


@pytest.mark.asyncio
async def test_delete_old_logs(site_service: SiteService, verified_user: UserModel):
    site_url = 'https://www.youtube.com'

    checker = await site_service.add_checker(user_id=verified_user.id, site_url=site_url)

    log_recent = await site_service.log(checker_id=checker.id, status_code=200, response_time_ms=80)
    log_old = await site_service.log(checker_id=checker.id, status_code=404, response_time_ms=0)

    old_time = datetime.now(timezone.utc) - timedelta(hours=26)
    await site_service.db.execute(
        update(CheckerLogModel)
        .where(CheckerLogModel.id == log_old.id)
        .values(created_at=old_time)
    )
    await site_service.db.commit()

    await site_service.delete_old_logs()

    result = await site_service.db.execute(select(CheckerLogModel))
    remaining_logs = result.scalars().all()
    
    assert len(remaining_logs) == 1
    assert remaining_logs[0].id == log_recent.id


@pytest.mark.asyncio
async def test_create_site_checker_fails_checker_already_exists(site_service: SiteService, verified_user: UserModel):
    site_url = 'https://www.youtube.com'

    await site_service.add_checker(user_id=verified_user.id, site_url=site_url)

    with pytest.raises(CheckerAlreadyExistsException):
        await site_service.add_checker(user_id=verified_user.id, site_url=site_url)


@pytest.mark.asyncio
async def test_delete_site_checker_fails_checker_not_found(site_service: SiteService, verified_user: UserModel):
    not_existed_id = 'not_existed_id'

    with pytest.raises(CheckerNotFoundException):
        await site_service.delete_checker(user_id=verified_user.id, checker_id=not_existed_id)


@pytest.mark.asyncio
async def test_get_all_last_24h_logs_fails_checker_not_found(site_service: SiteService, verified_user: UserModel):
    not_existed_id = 'not_existed_id'

    with pytest.raises(CheckerNotFoundException):
        await site_service.get_all_last_24h_logs(user_id=verified_user.id, checker_id=not_existed_id)