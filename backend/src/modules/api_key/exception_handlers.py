from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from .exceptions import *


def register_api_key_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIKeyNotFoundException)
    async def api_key_not_found_handler(request: Request, exc: APIKeyNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "API key not found"}
        )

    @app.exception_handler(NoAPIKeyInQueryException)
    async def no_api_key_in_query_handler(request: Request, exc: NoAPIKeyInQueryException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "No API key in query params"}
        )

    @app.exception_handler(BadAPIKeyException)
    async def bad_api_key_handler(request: Request, exc: BadAPIKeyException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Bad or not active API key"}
        )
