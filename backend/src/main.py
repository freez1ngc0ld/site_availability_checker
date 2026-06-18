from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.logger import setup_logger
from src.modules.auth.exception_handlers import register_auth_exception_handlers
from src.modules.site_checker.exception_handlers import register_site_exception_handlers
from src.modules.api_key.exception_handlers import register_api_key_exception_handlers
from src.modules.public_api.app import api_app
from src.modules.auth.router import router as router_for_auth
from src.modules.site_checker.router import router as router_for_site
from src.modules.api_key.router import router as router_for_api_keys
import uvicorn


app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)

app.include_router(router_for_auth)
app.include_router(router_for_site)
app.include_router(router_for_api_keys)

register_auth_exception_handlers(app)
register_site_exception_handlers(app)
register_api_key_exception_handlers(app)

app.mount(path='/api', app=api_app)

setup_logger()

if __name__ == '__main__':
    uvicorn.run(app='src.main:app', host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)
