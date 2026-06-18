from fastapi import BackgroundTasks
from src.core.security import UserTokenManager
from src.core.security import token_types
from src.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import StatusSchema, AccessTokenSchema, RedirectSchema
from .models import UserModel
from .exceptions import *
from .repositories import UserRepository
from .email import email_service
from random import randint
import httpx
import urllib.parse
import jwt
import hashlib
from loguru import logger


class AuthService:
    def __init__(self, db: AsyncSession):
        self.token_manager = UserTokenManager(secret_key=settings.SECRET_KEY)
        self.user_repo = UserRepository(db=db)
        self.db = db

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self.hash_password(password) == hashed_password

    def check_user_basic_exceptions(self, user: UserModel):
        if not user:
            raise UserNotFoundException()
        if not user.is_active:
            raise UserBannedException()
        if not user.is_verified:
            raise UserNotVerificatedException()

    async def create_user_with_password(self, background_tasks: BackgroundTasks, email: str, password: str) -> StatusSchema:
        user_exists = await self.user_repo.get_first(email=email)
        if user_exists:
            raise UserAlreadyExistsException()
        
        user = await self.user_repo.create(email=email, hashed_password=self.hash_password(password))

        await self.db.commit()

        logger.info('Registered new user. User ID: {user_id}', user_id=user.id)

        token = self.generate_token(
            user_id=user.id,
            token_type=token_types.VERIFICATION
        )

        background_tasks.add_task(
            email_service.send_token_email, 
            email=user.email, 
            token=token,
            token_type=token_types.VERIFICATION
        )

        return StatusSchema(status='Check your email and click on the link to verify account')
    
    async def login_user_with_password(self, email: str, password: str) -> AccessTokenSchema:
        user = await self.user_repo.get_first(email=email)
        
        self.check_user_basic_exceptions(user=user)
        
        if not self.verify_password(password, user.hashed_password):
            raise InvalidPasswordException()
        
        token = self.generate_token(
            user_id=user.id,
            token_type=token_types.AUTHORIZATION
        )

        logger.info('User logged in. User ID: {user_id}', user_id=user.id)

        return AccessTokenSchema(access_token=token)
    
    def generate_token(self, user_id: str, token_type: str) -> str:
        if token_type == token_types.AUTHORIZATION:
            expire = settings.ACCESS_AUTH_TOKEN_EXPIRE_SECONDS
        else:
            expire = settings.ACCESS_TOKEN_EXPIRE_SECONDS
        token = self.token_manager.generate_new_token(
            user_id=user_id,
            expires_in_seconds=expire,
            token_type=token_type
        )
        return token
    
    def check_token(self, token: str) -> tuple[str, str]:
        payload = self.token_manager.verify_token(token)
        if not payload:
            raise InvalidTokenTypeException()
        user_id, exp, token_type = payload.get('sub'), payload.get('exp'), payload.get('token_type')
        if not user_id or not exp or not token_type:
            raise InvalidTokenTypeException()
        if len(payload.keys()) != 3:
            raise InvalidTokenTypeException()
        return user_id, token_type
    
    async def verification(self, token: str) -> AccessTokenSchema:
        user_id, token_type = self.check_token(token)

        if token_type != token_types.VERIFICATION:
            raise InvalidTokenTypeException()
        
        user = await self.user_repo.get_by_pk(pk=user_id)
        if not user:
            raise UserNotFoundException()
        if not user.is_active:
            raise UserBannedException()
        if user.is_verified:
            raise UserAlreadyVerificatedException()

        user.is_verified = True

        await self.db.commit()

        logger.info('User verified. User ID: {user_id}', user_id=user.id)

        token = self.generate_token(
            user_id=user.id,
            token_type=token_types.AUTHORIZATION
        )

        return AccessTokenSchema(access_token=token)
    
    async def request_password_reset(self, background_tasks: BackgroundTasks, email: str) -> StatusSchema:
        user = await self.user_repo.get_first(email=email)

        self.check_user_basic_exceptions(user=user)

        token = self.generate_token(
            user_id=user.id,
            token_type=token_types.PASSWORD_CHANGE
        )
        background_tasks.add_task(
            email_service.send_token_email, 
            email=user.email, 
            token=token,
            token_type=token_types.PASSWORD_CHANGE
        )
        return StatusSchema(status='Check your email and click on the link to change password')
    
    async def confirm_password_reset(self, token: str, new_password: str) -> StatusSchema:
        user_id, token_type = self.check_token(token)

        if token_type != token_types.PASSWORD_CHANGE:
            raise InvalidTokenTypeException()
        
        user = await self.user_repo.get_by_pk(pk=user_id)

        self.check_user_basic_exceptions(user=user)
        
        user.hashed_password = self.hash_password(new_password)

        await self.db.commit()

        logger.info('User changed password. User ID: {user_id}', user_id=user.id)

        return StatusSchema(status='Password changed successfully')

    async def request_account_delete(self, user_id: str, background_tasks: BackgroundTasks) -> AccessTokenSchema:
        user = await self.user_repo.get_by_pk(pk=user_id)

        self.check_user_basic_exceptions(user=user)

        otp_code = f'{randint(100000, 999999)}'
        packed_user_id = f'{user_id}:{otp_code}'
        background_tasks.add_task(
            email_service.send_code_email, 
            email=user.email, 
            otp=otp_code
        )
        token = self.generate_token(
            user_id=packed_user_id,
            token_type=token_types.ACCOUNT_DELETE
        )
        return AccessTokenSchema(access_token=token)

    async def confirm_account_delete(self, token: str, user_otp: str, user_id: str) -> StatusSchema:
        user_id_and_otp, token_type = self.check_token(token)

        if token_type != token_types.ACCOUNT_DELETE:
            raise InvalidTokenTypeException()
        try:
            unpacked_user_id, token_otp = user_id_and_otp.split(':')
        except ValueError:
            raise InvalidTokenTypeException()
        
        if user_id != unpacked_user_id:
            raise InvalidTokenTypeException()
        if token_otp != user_otp:
            raise InvalidOTPException()
        
        user = await self.user_repo.get_by_pk(pk=user_id)

        self.check_user_basic_exceptions(user=user)

        await self.user_repo.delete(pk=user_id) 
        await self.db.commit()

        logger.info('User deleted account. User ID: {user_id}', user_id=user.id)
        
        return StatusSchema(status='Account deleted successfully')
    
    def generate_google_oauth2_link(self) -> RedirectSchema:
        query = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': f'http://{settings.FRONTEND_HOST}:{settings.FRONTEND_PORT}/auth/google',
            'response_type': 'code',
            'scope': ' '.join(['openid', 'email'])
        }
        query_str = urllib.parse.urlencode(query, quote_via=urllib.parse.quote)
        oauth2_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        return RedirectSchema(url=f'{oauth2_url}?{query_str}')
    
    async def google_login(self, code: str) -> AccessTokenSchema:
        google_token_url = 'https://oauth2.googleapis.com/token'

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=google_token_url,
                params={
                    'client_id': settings.GOOGLE_CLIENT_ID,
                    'client_secret': settings.GOOGLE_CLIENT_SECRET,
                    'grant_type': 'authorization_code',
                    'redirect_uri': f'http://{settings.FRONTEND_HOST}:{settings.FRONTEND_PORT}/auth/google',
                    'code': code
                }
            ) 
            if 'application/json' not in response.headers.get('Content-Type', ''):
                raise NotJSONResponseException()
            res = response.json()
            id_token = res.get('id_token')

            if not id_token:
                raise MissingIDTokenException()
            
            try:
                payload = jwt.decode(id_token, options={'verify_signature': False})
            except jwt.DecodeError:
                raise InvalidTokenTypeException()
            
            google_id = payload.get('sub')     
            email = payload.get('email')         

            user = await self.user_repo.get_first(email=email)
            if not user:
                user = await self.user_repo.create(email=email, google_id=google_id, is_verified=True)
                logger.info('Registered new user. User ID: {user_id}', user_id=user.id)
            else:
                if not user.is_active:
                    raise UserBannedException()
                user.google_id = google_id
                user.is_verified = True
                logger.info('User logged in. User ID: {user_id}', user_id=user.id)

            token = self.generate_token(
                user_id=user.id, 
                token_type=token_types.AUTHORIZATION
            )
            await self.db.commit()

            return AccessTokenSchema(access_token=token)
