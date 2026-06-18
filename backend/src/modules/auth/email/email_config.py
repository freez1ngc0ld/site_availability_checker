from fastapi_mail import ConnectionConfig
from src.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_ADDRESS,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.SMTP_ADDRESS,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)