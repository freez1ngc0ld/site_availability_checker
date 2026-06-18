import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from datetime import datetime, timedelta, timezone
from src.modules.api_key.models import APIKeyModel
from src.modules.auth.models import UserModel
from src.modules.api_key.service import APIKeyService
from src.modules.auth.service import AuthService
from fastapi import status


@pytest.mark.asyncio
async def test_get_api_keys_empty(client: AsyncClient, auth_headers):
    response = await client.get("/api_keys", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_api_key_success(client: AsyncClient, auth_headers, get_db):
    response = await client.post("/api_keys", headers=auth_headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "key" in data
    assert isinstance(data["key"], str)

    result = await get_db.execute(select(APIKeyModel).where(APIKeyModel.key == data["key"]))
    db_key = result.scalar_one_or_none()
    assert db_key is not None
    assert db_key.key == data["key"]


@pytest.mark.asyncio
async def test_get_api_keys_pagination(client: AsyncClient, auth_headers, api_key_service: APIKeyService, verified_user: UserModel, get_db):
    k1 = await api_key_service.create_api_key(user_id=verified_user.id)
    k2 = await api_key_service.create_api_key(user_id=verified_user.id)
    k3 = await api_key_service.create_api_key(user_id=verified_user.id)

    now = datetime.now(timezone.utc)
    await get_db.execute(update(APIKeyModel).where(APIKeyModel.key == k1.key).values(created_at=now - timedelta(seconds=2)))
    await get_db.execute(update(APIKeyModel).where(APIKeyModel.key == k2.key).values(created_at=now - timedelta(seconds=1)))
    await get_db.execute(update(APIKeyModel).where(APIKeyModel.key == k3.key).values(created_at=now))
    await get_db.commit()

    response_limit = await client.get("/api_keys", params={"limit": "2"}, headers=auth_headers)
    assert response_limit.status_code == status.HTTP_200_OK
    assert len(response_limit.json()) == 2
    assert response_limit.json()[0]["key"] == k1.key

    response_offset = await client.get("/api_keys", params={"limit": "2", "offset": "2"}, headers=auth_headers)
    assert response_offset.status_code == status.HTTP_200_OK
    assert len(response_offset.json()) == 1
    assert response_offset.json()[0]["key"] == k3.key


@pytest.mark.asyncio
async def test_delete_api_key_success(client: AsyncClient, auth_headers, api_key_service: APIKeyService, verified_user: UserModel, get_db):
    new_key_schema = await api_key_service.create_api_key(user_id=verified_user.id)
    target_key = new_key_schema.key

    response = await client.delete(f"/api_keys/{target_key}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    result = await get_db.execute(select(APIKeyModel).where(APIKeyModel.key == target_key))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_api_key_not_found(client: AsyncClient, auth_headers):
    fake_key = "some-fake-unexistent-key-67"
    response = await client.delete(f"/api_keys/{fake_key}", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_other_user_api_key(client: AsyncClient, auth_headers, api_key_service: APIKeyService, auth_service: AuthService):
    other_user = await auth_service.user_repo.create(
        email='diddy@island.us',
        hashed_password=auth_service.hash_password('12345678'),
        is_verified=True,
        is_active=True
    )
    await auth_service.db.commit()

    other_user_key_schema = await api_key_service.create_api_key(user_id=other_user.id)
    other_key = other_user_key_schema.key

    response = await client.delete(f"/api_keys/{other_key}", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
