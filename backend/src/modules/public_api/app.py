from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.modules.auth.exception_handlers import register_auth_exception_handlers
from src.modules.site_checker.exception_handlers import register_site_exception_handlers
from src.modules.api_key.exception_handlers import register_api_key_exception_handlers
from .router import router
from src.core.config import settings

api_app = FastAPI(title=f'{settings.APP_NAME} Public API', version=settings.VERSION)
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

api_app.include_router(router)

register_auth_exception_handlers(api_app)
register_site_exception_handlers(api_app)
register_api_key_exception_handlers(api_app)

