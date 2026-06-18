import pytest
from src.modules.api_key.service import APIKeyService
from src.modules.api_key.exceptions import *
from src.modules.auth.models import UserModel


@pytest.mark.asyncio
async def test_create_api_key(api_key_service: APIKeyService, verified_user: UserModel):
    api_key = await api_key_service.create_api_key(user_id=verified_user.id)
    api_key_from_db = await api_key_service.api_repo.get_first(key=api_key.key)

    assert api_key_from_db is not None
    assert api_key_from_db.user_id == verified_user.id


@pytest.mark.asyncio
async def test_get_user_api_keys_success(api_key_service: APIKeyService, verified_user: UserModel):
    created_key = await api_key_service.create_api_key(user_id=verified_user.id)

    user_keys = await api_key_service.get_user_api_keys(user_id=verified_user.id, limit=None, offset=None)

    assert len(user_keys) == 1
    assert user_keys[0].key == created_key.key


@pytest.mark.asyncio
async def test_get_api_keys_pagination_success(api_key_service: APIKeyService, verified_user: UserModel):
    for _ in range(3):
        await api_key_service.create_api_key(user_id=verified_user.id)

    all_keys = await api_key_service.get_user_api_keys(user_id=verified_user.id, limit=None, offset=None)
    assert len(all_keys) == 3

    keys_l2_o0 = await api_key_service.get_user_api_keys(user_id=verified_user.id, limit=2, offset=0)
    assert keys_l2_o0 == all_keys[0:2]

    keys_l2_o1 = await api_key_service.get_user_api_keys(user_id=verified_user.id, limit=2, offset=1)
    assert keys_l2_o1 == all_keys[1:3]

    keys_lno2 = await api_key_service.get_user_api_keys(user_id=verified_user.id, limit=None, offset=2)
    assert keys_lno2 == all_keys[2:3]


@pytest.mark.asyncio
async def test_delete_api_key_success(api_key_service: APIKeyService, verified_user: UserModel):
    api_key = await api_key_service.create_api_key(user_id=verified_user.id)

    await api_key_service.delete_api_key(user_id=verified_user.id, api_key=api_key.key)

    api_key_from_db = await api_key_service.api_repo.get_first(key=api_key.key)
    assert api_key_from_db is None


@pytest.mark.asyncio
async def test_delete_api_key_not_found(api_key_service: APIKeyService, verified_user: UserModel):
    invalid_key = "non_existent_key"

    with pytest.raises(APIKeyNotFoundException):
        await api_key_service.delete_api_key(user_id=verified_user.id, api_key=invalid_key)
