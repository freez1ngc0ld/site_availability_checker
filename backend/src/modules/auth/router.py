from fastapi import APIRouter, status, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from .dependencies import get_auth_service, get_current_user
from .service import AuthService
from .models import UserModel
from .schemas import (
    UserCreatePassword, 
    AccessTokenSchema,
    StatusSchema, 
    RequestResetSchema, 
    ConfirmResetSchema, 
    ConfirmDeleteAccount,
    VerificationSchema,
    RedirectSchema
)

router = APIRouter(prefix='/auth', tags=['Auth'])

@router.post('/registration', status_code=status.HTTP_201_CREATED, response_model=StatusSchema)
async def create_user(background_tasks: BackgroundTasks, payload: UserCreatePassword, auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.create_user_with_password(email=payload.email, password=payload.password, background_tasks=background_tasks)

@router.post('/login', status_code=status.HTTP_200_OK, response_model=AccessTokenSchema)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),  
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.login_user_with_password(email=form_data.username, password=form_data.password)

@router.post('/verificate', status_code=status.HTTP_200_OK, response_model=AccessTokenSchema)
async def verificate(payload: VerificationSchema, auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.verification(token=payload.access_token)

@router.patch('/reset-password/request', status_code=status.HTTP_200_OK, response_model=StatusSchema)
async def reset_request(background_tasks: BackgroundTasks, payload: RequestResetSchema, auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.request_password_reset(email=payload.email, background_tasks=background_tasks)

@router.patch('/reset-password/confirm', status_code=status.HTTP_200_OK, response_model=StatusSchema)
async def reset_confirm(payload: ConfirmResetSchema, auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.confirm_password_reset(token=payload.access_token, new_password=payload.new_password)

@router.delete('/delete-account/request', status_code=status.HTTP_200_OK, response_model=AccessTokenSchema)
async def delete_request(background_tasks: BackgroundTasks, auth_service: AuthService = Depends(get_auth_service), user: UserModel = Depends(get_current_user)):
    return await auth_service.request_account_delete(user_id=user.id, background_tasks=background_tasks)

@router.delete('/delete-account/confirm', status_code=status.HTTP_200_OK, response_model=StatusSchema)
async def delete_confirm(payload: ConfirmDeleteAccount, auth_service: AuthService = Depends(get_auth_service), user: UserModel = Depends(get_current_user)):
    return await auth_service.confirm_account_delete(user_id=user.id, user_otp=payload.one_time_password, token=payload.access_token)

@router.get('/google/url', status_code=status.HTTP_200_OK, response_model=RedirectSchema)
def get_google_ouath2_link(auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.generate_google_oauth2_link()

@router.post('/google/login', status_code=status.HTTP_200_OK, response_model=AccessTokenSchema)
async def google_login(code: str, auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.google_login(code=code)
