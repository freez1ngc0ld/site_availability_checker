from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from .exceptions import *
from loguru import logger


def register_site_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CheckerNotFoundException)
    async def site_not_found_handler(request: Request, exc: CheckerNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Site checker not found"}
        )

    @app.exception_handler(CheckerAlreadyExistsException)
    async def site_already_exists_handler(request: Request, exc: CheckerAlreadyExistsException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Site checker already exists"}
        )

    @app.exception_handler(DeletingErrorException)
    async def deleting_error_handler(request: Request, exc: DeletingErrorException):
        logger.error(
            "Something went wrong with delete site checker. IP: {client_host} | Path: {path}",
            client_host=request.client.host if request.client else "unknown",
            path=request.url.path
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Something went wrong with delete site checker"}
        )
