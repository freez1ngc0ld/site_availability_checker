import time
from typing import Any
import jwt
from src.modules.auth.exceptions import TokenExpireException


class UserTokenManager:
    def __init__(self, secret_key: str) -> None:
        self.__secret_key: str = secret_key
        self.__algorithm: str = "HS256"  

    def generate_new_token(self, user_id: str, expires_in_seconds: int, token_type: str) -> str:
        payload = {
            "sub": user_id,
            "exp": int(time.time()) + expires_in_seconds,
            "token_type": token_type
        }
        return jwt.encode(payload, self.__secret_key, algorithm=self.__algorithm)
    
    def verify_token(self, token: str) -> dict[str, Any] | None:
        try:
            return jwt.decode(token, self.__secret_key, algorithms=[self.__algorithm])
        except jwt.ExpiredSignatureError:
            raise TokenExpireException()
        except jwt.PyJWTError:
            return None
