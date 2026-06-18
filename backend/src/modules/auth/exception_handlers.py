from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from .exceptions import *
from loguru import logger


def register_auth_exception_handlers(app: FastAPI):
    @app.exception_handler(UserNotFoundException)
    async def user_not_found_handler(request: Request, exc: UserNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "User not found"}
        )

    @app.exception_handler(UserAlreadyExistsException)
    async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "User already exists"}
        )

    @app.exception_handler(UserNotVerificatedException)
    async def user_not_verificated_handler(request: Request, exc: UserNotVerificatedException):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "You are not verificated"}
        )

    @app.exception_handler(UserAlreadyVerificatedException)
    async def user_already_verificated_handler(request: Request, exc: UserAlreadyVerificatedException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "You are already activated"}
        )

    @app.exception_handler(UserBannedException)
    async def user_banned_handler(request: Request, exc: UserBannedException):
        logger.warning(
            "Banned user attempted to access the system. IP: {client_host} | Path: {path}",
            client_host=request.client.host if request.client else "unknown",
            path=request.url.path
        )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "You have been banned lol suck my dick loser"}
        )

    @app.exception_handler(InvalidPasswordException)
    async def invalid_password_handler(request: Request, exc: InvalidPasswordException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid password"}
        )
    
    @app.exception_handler(InvalidOTPException)
    async def invalid_otp_handler(request: Request, exc: InvalidOTPException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid 6-digits code"}
        )

    @app.exception_handler(TokenExpireException)
    async def token_expire_handler(request: Request, exc: TokenExpireException):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Too late, try again"}
        )

    @app.exception_handler(InvalidTokenTypeException)
    async def invalid_token_type_handler(request: Request, exc: InvalidTokenTypeException):
        logger.warning(
            "Invalid JWT token submitted. IP: {client_host}", 
            client_host=request.client.host if request.client else "unknown"
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid Token"},
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    @app.exception_handler(NotJSONResponseException)
    async def not_json_response(request: Request, exc: NotJSONResponseException):
        logger.error("OAuth external provider returned non-JSON data on {path}", path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Not JSON Response"},
        )
    @app.exception_handler(MissingIDTokenException)
    async def missing_id_token(request: Request, exc: MissingIDTokenException):
        logger.warning("OAuth handshake failed: missing id_token in provider response")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing ID Token"},
        )
    
    @app.exception_handler(Exception)
    async def global_internal_server_error_handler(request: Request, exc: Exception):
        logger.exception("CRITICAL SERVER ERROR on {method} {path}", method=request.method, path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )
