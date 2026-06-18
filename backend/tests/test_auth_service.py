import pytest
from src.modules.auth.service import AuthService
from src.core.security import token_types
from unittest.mock import MagicMock
from src.modules.auth.exceptions import *
from src.modules.auth.models import UserModel
from src.core.config import settings
import jwt
import time


@pytest.mark.asyncio
async def test_successful_user_auth_flow(auth_service: AuthService, mock_bg_tasks: MagicMock):
    email = 'bigjeff@island.us'
    password = '12345678'

    reg_result = await auth_service.create_user_with_password(
        background_tasks=mock_bg_tasks, email=email, password=password
    )

    assert reg_result.status == 'Check your email and click on the link to verify account'
    assert mock_bg_tasks.add_task.called

    token = mock_bg_tasks.add_task.call_args.kwargs.get('token')

    verify_result = await auth_service.verification(token=token)
    user = await auth_service.user_repo.get_first(email=email)

    assert user.is_verified is True
    assert auth_service.check_token(verify_result.access_token)[1] == token_types.AUTHORIZATION

    auth_result = await auth_service.login_user_with_password(email=email, password=password)
    assert auth_service.check_token(auth_result.access_token)[1] == token_types.AUTHORIZATION

    
@pytest.mark.asyncio
async def test_reset_user_password(auth_service: AuthService, mock_bg_tasks: MagicMock, verified_user: UserModel):
    new_password = 'new_12345678'

    request_result = await auth_service.request_password_reset(email=verified_user.email, background_tasks=mock_bg_tasks)

    assert request_result.status == 'Check your email and click on the link to change password'
    assert mock_bg_tasks.add_task.called

    token = mock_bg_tasks.add_task.call_args.kwargs.get('token')
    assert auth_service.check_token(token)[1] == token_types.PASSWORD_CHANGE

    confirm_result = await auth_service.confirm_password_reset(token=token, new_password=new_password)

    assert confirm_result.status == 'Password changed successfully'

    user = await auth_service.user_repo.get_first(email=verified_user.email)
    assert auth_service.verify_password(password=new_password, hashed_password=user.hashed_password)


@pytest.mark.asyncio
async def test_delete_account(auth_service: AuthService, mock_bg_tasks: MagicMock, verified_user: UserModel):
    request_result = await auth_service.request_account_delete(user_id=verified_user.id, background_tasks=mock_bg_tasks)
    token = request_result.access_token

    assert mock_bg_tasks.add_task.called

    otp_code = mock_bg_tasks.add_task.call_args.kwargs.get('otp')

    confirm_result = await auth_service.confirm_account_delete(token=token, user_otp=otp_code, user_id=verified_user.id)
    
    assert confirm_result.status == 'Account deleted successfully'

    user = await auth_service.user_repo.get_first(email=verified_user.email)
    assert user is None


@pytest.mark.asyncio
async def test_registration_fails_with_user_already_exists(auth_service: AuthService, mock_bg_tasks: MagicMock, verified_user: UserModel):
    with pytest.raises(UserAlreadyExistsException):
        await auth_service.create_user_with_password(
            email=verified_user.email, password='12345678', background_tasks=mock_bg_tasks
        )


@pytest.mark.asyncio
async def test_login_fails_with_not_exist_user(auth_service: AuthService):
    not_exist_email = 'notbigjeff@island.us'
    password = '12345678'

    with pytest.raises(UserNotFoundException):
        await auth_service.login_user_with_password(email=not_exist_email, password=password)


@pytest.mark.asyncio
async def test_login_fails_with_invalid_password(auth_service: AuthService, verified_user: UserModel):
    wrong_password = 'wrong_12345678'

    with pytest.raises(InvalidPasswordException):
        await auth_service.login_user_with_password(email=verified_user.email, password=wrong_password)


@pytest.mark.asyncio
async def test_login_fails_on_banned_user(auth_service: AuthService):
    email = 'bannedbigjeff@island.us'
    password = '12345678'

    await auth_service.user_repo.create(
        email=email,
        hashed_password=auth_service.hash_password(password),
        is_active=False
    )

    with pytest.raises(UserBannedException):
        await auth_service.login_user_with_password(email=email, password=password)


@pytest.mark.asyncio
async def test_login_fails_on_not_verified_user(auth_service: AuthService):
    email = 'unverifiedbigjeff@island.us'
    password = '12345678'

    await auth_service.user_repo.create(
        email=email,
        hashed_password=auth_service.hash_password(password),
        is_verified=False
    )

    with pytest.raises(UserNotVerificatedException):
        await auth_service.login_user_with_password(email=email, password=password)


def test_check_token_fails_with_invalid_string(auth_service: AuthService):
    bad_token = '6ad_7oken'
    
    with pytest.raises(InvalidTokenTypeException):
        auth_service.check_token(bad_token)


def test_check_token_fails_with_wrong_payload_keys(auth_service: AuthService):
    bad_payload = {
        'sub1': 'userid',
        'exp1': int(time.time()) + 300, 
        'token_type1': token_types.AUTHORIZATION
    }
    bad_token = jwt.encode(payload=bad_payload, key=settings.SECRET_KEY, algorithm='HS256')

    with pytest.raises(InvalidTokenTypeException):
        auth_service.check_token(bad_token)


def test_check_token_fails_with_extra_parameters(auth_service: AuthService):
    bad_payload = {
        'sub': 'userid',
        'exp': int(time.time()) + 300, 
        'token_type': token_types.AUTHORIZATION,
        'bad_parameter': '67'
    }
    bad_token = jwt.encode(payload=bad_payload, key=settings.SECRET_KEY, algorithm='HS256')

    with pytest.raises(InvalidTokenTypeException):
        auth_service.check_token(bad_token)


def test_check_token_success(auth_service: AuthService):
    good_payload = {
        'sub': 'userid',
        'exp': int(time.time()) + 300, 
        'token_type': token_types.AUTHORIZATION,
    }
    good_token = jwt.encode(payload=good_payload, key=settings.SECRET_KEY, algorithm='HS256')

    user_id, token_type = auth_service.check_token(good_token)

    assert user_id == 'userid'
    assert token_type == token_types.AUTHORIZATION


@pytest.mark.asyncio
async def test_verification_fails_with_invalid_token_type(auth_service: AuthService, verified_user: UserModel):
    bad_token = auth_service.generate_token(user_id=verified_user.id, token_type=token_types.AUTHORIZATION)

    with pytest.raises(InvalidTokenTypeException):
        await auth_service.verification(bad_token)


@pytest.mark.asyncio
async def test_verification_fails_with_not_exist_user(auth_service: AuthService):
    bad_token = auth_service.generate_token(user_id='not-existed-user', token_type=token_types.VERIFICATION)

    with pytest.raises(UserNotFoundException):
        await auth_service.verification(bad_token)


@pytest.mark.asyncio
async def test_verification_fails_if_already_verified(auth_service: AuthService, verified_user: UserModel):
    good_token = auth_service.generate_token(user_id=verified_user.id, token_type=token_types.VERIFICATION)

    with pytest.raises(UserAlreadyVerificatedException):
        await auth_service.verification(good_token)


@pytest.mark.asyncio
async def test_verification_fails_with_banned_user(auth_service: AuthService):
    email = 'bannedbigjeff@island.us'
    user = await auth_service.user_repo.create(
        email=email, 
        hashed_password=auth_service.hash_password('12345678'),
        is_verified=False,
        is_active=False
    )
    good_token = auth_service.generate_token(user_id=user.id, token_type=token_types.VERIFICATION)

    with pytest.raises(UserBannedException):
        await auth_service.verification(good_token)


@pytest.mark.asyncio
async def test_password_reset_fails_with_not_exist_user(auth_service: AuthService, mock_bg_tasks: MagicMock):
    not_existed_email = 'notexistedbigjeff@island.us'

    with pytest.raises(UserNotFoundException):
        await auth_service.request_password_reset(email=not_existed_email, background_tasks=mock_bg_tasks)


@pytest.mark.asyncio
async def test_password_reset_fails_if_not_verified(auth_service: AuthService, mock_bg_tasks: MagicMock):
    email = 'notverifiedbigjeff@island.us'
    await auth_service.user_repo.create(
        email=email, 
        hashed_password=auth_service.hash_password('12345678'),
        is_verified=False
    )

    with pytest.raises(UserNotVerificatedException):
        await auth_service.request_password_reset(email=email, background_tasks=mock_bg_tasks)


@pytest.mark.asyncio
async def test_password_reset_fails_with_banned_user(auth_service: AuthService, mock_bg_tasks: MagicMock):
    email = 'bannedbigjeff@island.us'
    await auth_service.user_repo.create(
        email=email, 
        hashed_password=auth_service.hash_password('12345678'),
        is_verified=True,
        is_active=False
    )

    with pytest.raises(UserBannedException):
        await auth_service.request_password_reset(email=email, background_tasks=mock_bg_tasks)


@pytest.mark.asyncio
async def test_password_reset_fails_with_invalid_token_type(auth_service: AuthService, verified_user: UserModel):
    bad_token = auth_service.generate_token(user_id=verified_user.id, token_type=token_types.AUTHORIZATION)

    with pytest.raises(InvalidTokenTypeException):
        await auth_service.confirm_password_reset(token=bad_token, new_password='new-12345678')


@pytest.mark.asyncio
async def test_account_delete_fails_with_not_exist_user(auth_service: AuthService, mock_bg_tasks: MagicMock):
    not_existed_user_id = 'bigjeff'

    with pytest.raises(UserNotFoundException):
        await auth_service.request_account_delete(user_id=not_existed_user_id, background_tasks=mock_bg_tasks)


@pytest.mark.asyncio
async def test_account_delete_fails_if_not_verified(auth_service: AuthService, mock_bg_tasks: MagicMock):
    email = 'notverifiedbigjeff@island.us'
    user = await auth_service.user_repo.create(
        email=email, 
        hashed_password=auth_service.hash_password('12345678'),
        is_verified=False
    )

    with pytest.raises(UserNotVerificatedException):
        await auth_service.request_account_delete(user_id=user.id, background_tasks=mock_bg_tasks)


@pytest.mark.asyncio
async def test_account_delete_fails_with_banned_user(auth_service: AuthService, mock_bg_tasks: MagicMock):
    email = 'bannedbigjeff@island.us'
    user = await auth_service.user_repo.create(
        email=email, 
        hashed_password=auth_service.hash_password('12345678'),
        is_verified=True,
        is_active=False
    )

    with pytest.raises(UserBannedException):
        await auth_service.request_account_delete(user_id=user.id, background_tasks=mock_bg_tasks)


@pytest.mark.asyncio
async def test_account_delete_fails_with_invalid_token_type_token_error(auth_service: AuthService, verified_user: UserModel):
    otp = '123456'
    bad_token = auth_service.generate_token(user_id=f'{verified_user.id}:{otp}', token_type=token_types.AUTHORIZATION)

    with pytest.raises(InvalidTokenTypeException):
        await auth_service.confirm_account_delete(token=bad_token, user_id=verified_user.id, user_otp=otp)


@pytest.mark.asyncio
async def test_account_delete_fails_with_invalid_token_type_otp_parsing_error(auth_service: AuthService, verified_user: UserModel):
    otp = '123456'
    bad_token = auth_service.generate_token(user_id=f'{verified_user.id}{otp}', token_type=token_types.ACCOUNT_DELETE)

    with pytest.raises(InvalidTokenTypeException):
        await auth_service.confirm_account_delete(token=bad_token, user_id=verified_user.id, user_otp=otp)


@pytest.mark.asyncio
async def test_account_delete_fails_with_invalid_token_type_invalid_user_id(auth_service: AuthService, verified_user: UserModel):
    otp = '123456'
    bad_token = auth_service.generate_token(user_id=f'{verified_user.id + "67"}:{otp}', token_type=token_types.ACCOUNT_DELETE)

    with pytest.raises(InvalidTokenTypeException):
        await auth_service.confirm_account_delete(token=bad_token, user_id=verified_user.id, user_otp=otp)


@pytest.mark.asyncio
async def test_account_delete_fails_with_invalid_otp(auth_service: AuthService, verified_user: UserModel):
    otp = '123456'
    bad_token = auth_service.generate_token(user_id=f'{verified_user.id}:123467', token_type=token_types.ACCOUNT_DELETE)

    with pytest.raises(InvalidOTPException):
        await auth_service.confirm_account_delete(token=bad_token, user_id=verified_user.id, user_otp=otp)