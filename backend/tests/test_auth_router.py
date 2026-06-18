import pytest
from httpx import AsyncClient
from sqlalchemy import select
from src.modules.auth.models import UserModel
from src.modules.auth.service import AuthService
from src.core.security import token_types
from fastapi import status


@pytest.mark.asyncio
async def test_api_registration_success(client: AsyncClient, get_db):
    payload = {
        'email': 'bigjeff@island.us',
        'password': '12345678'
    }
    response = await client.post('/auth/registration', json=payload)
    
    assert response.status_code == status.HTTP_201_CREATED
    assert 'Check your email' in response.json()['status']

    result = await get_db.execute(select(UserModel).where(UserModel.email == payload['email']))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.is_verified is False


@pytest.mark.asyncio
async def test_api_login_success(client: AsyncClient, verified_user: UserModel):
    form_data = {
        'username': verified_user.email,  
        'password': '12345678'
    }
    response = await client.post('/auth/login', data=form_data)
    
    assert response.status_code == status.HTTP_200_OK
    assert 'access_token' in response.json()


@pytest.mark.asyncio
async def test_api_verification_success(client: AsyncClient, auth_service: AuthService, get_db):
    user = await auth_service.user_repo.create(
        email='unverifiedbigjeff@island.us',
        hashed_password=auth_service.hash_password('12345678'),
        is_verified=False,
        is_active=True
    )
    await auth_service.db.commit()

    token = auth_service.generate_token(user_id=user.id, token_type=token_types.VERIFICATION)
    
    response = await client.post('/auth/verificate', json={'access_token': token})
    
    assert response.status_code == status.HTTP_200_OK
    assert 'access_token' in response.json()

    await get_db.refresh(user)
    assert user.is_verified is True


@pytest.mark.asyncio
async def test_api_reset_password_flow(client: AsyncClient, verified_user: UserModel, auth_service: AuthService, get_db):
    req_response = await client.patch('/auth/reset-password/request', json={'email': verified_user.email})
    assert req_response.status_code == status.HTTP_200_OK

    reset_token = auth_service.generate_token(user_id=verified_user.id, token_type=token_types.PASSWORD_CHANGE)

    new_password = 'new_12345678'

    confirm_payload = {
        'access_token': reset_token,
        'new_password': new_password
    }
    confirm_response = await client.patch('/auth/reset-password/confirm', json=confirm_payload)
    assert confirm_response.status_code == status.HTTP_200_OK

    await get_db.refresh(verified_user)
    assert auth_service.verify_password(new_password, verified_user.hashed_password)


@pytest.mark.asyncio
async def test_api_delete_account_flow(client: AsyncClient, verified_user: UserModel, auth_service: AuthService, get_db):
    auth_token = auth_service.generate_token(user_id=verified_user.id, token_type=token_types.AUTHORIZATION)
    headers = {'Authorization': f'Bearer {auth_token}'}

    req_response = await client.delete('/auth/delete-account/request', headers=headers)
    assert req_response.status_code == status.HTTP_200_OK

    otp_code = '123456'
    packed_user_id = f'{verified_user.id}:{otp_code}'
    delete_token = auth_service.generate_token(user_id=packed_user_id, token_type=token_types.ACCOUNT_DELETE)

    confirm_payload = {
        'one_time_password': otp_code,
        'access_token': delete_token
    }

    confirm_response = await client.request(
        method='DELETE',
        url='/auth/delete-account/confirm',
        json=confirm_payload,
        headers=headers
    )
    assert confirm_response.status_code == status.HTTP_200_OK

    result = await get_db.execute(select(UserModel).where(UserModel.id == verified_user.id))
    user_after_delete = result.scalar_one_or_none()
    assert user_after_delete is None


@pytest.mark.asyncio
async def test_api_registration_email_already_exists(client: AsyncClient, verified_user: UserModel):
    payload = {
        'email': verified_user.email,  
        'password': '12345678'
    }
    response = await client.post('/auth/registration', json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_api_login_invalid_password(client: AsyncClient, verified_user: UserModel):
    form_data = {
        'username': verified_user.email,
        'password': 'wrong_12345678'
    }
    response = await client.post('/auth/login', data=form_data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_api_login_user_not_found(client: AsyncClient):
    form_data = {
        'username': 'notbigjeff@island.us',
        'password': '12345678'
    }
    response = await client.post('/auth/login', data=form_data)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_api_verification_invalid_token_type(client: AsyncClient, verified_user: UserModel, auth_service: AuthService):

    bad_token = auth_service.generate_token(user_id=verified_user.id, token_type=token_types.AUTHORIZATION)
    
    response = await client.post('/auth/verificate', json={'access_token': bad_token})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_api_delete_request_unverified_user(client: AsyncClient, auth_service: AuthService):
    user = await auth_service.user_repo.create(
        email='bigjeff@island.us',
        hashed_password=auth_service.hash_password('12345678'),
        is_verified=False,
        is_active=True
    )
    await auth_service.db.commit()
    
    auth_token = auth_service.generate_token(user_id=user.id, token_type=token_types.AUTHORIZATION)
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    response = await client.delete('/auth/delete-account/request', headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_api_delete_account_confirm_wrong_otp(client: AsyncClient, verified_user: UserModel, auth_service: AuthService):
    auth_token = auth_service.generate_token(user_id=verified_user.id, token_type=token_types.AUTHORIZATION)
    headers = {'Authorization': f'Bearer {auth_token}'}

    correct_otp = '111111'
    packed_user_id = f'{verified_user.id}:{correct_otp}'
    delete_token = auth_service.generate_token(user_id=packed_user_id, token_type=token_types.ACCOUNT_DELETE)

    payload = {
        'one_time_password': '999999',
        'access_token': delete_token
    }
    
    response = await client.request(
        method='DELETE',
        url='/auth/delete-account/confirm',
        json=payload,
        headers=headers
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
