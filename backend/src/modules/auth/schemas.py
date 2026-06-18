from src.core.base.schema import BaseSchema
from pydantic import EmailStr
from datetime import datetime

class UserCreatePassword(BaseSchema):
    email: EmailStr
    password: str

class UserCreateGoogle(BaseSchema):
    email: EmailStr
    google_id: str

class VerificationSchema(BaseSchema):
    access_token: str

class RequestResetSchema(BaseSchema):
    email: EmailStr

class ConfirmResetSchema(BaseSchema):
    access_token: str
    new_password: str

class ConfirmDeleteAccount(BaseSchema):
    access_token: str
    one_time_password: str

class UserSchema(BaseSchema):
    id: str
    email: EmailStr
    google_id: str
    created_at: datetime

class AccessTokenSchema(BaseSchema):
    access_token: str
    token_type: str = "Bearer"

class StatusSchema(BaseSchema):
    status: str

class RedirectSchema(BaseSchema):
    url: str
