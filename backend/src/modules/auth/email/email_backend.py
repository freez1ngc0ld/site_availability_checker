from fastapi_mail import FastMail, MessageSchema, MessageType
from src.core.config import settings
from src.core.security import token_types
from ..exceptions import InvalidTokenTypeException
from .email_config import conf


class EmailService:
    def __init__(self):
        self.fastmail = FastMail(conf)

    async def send_token_email(self, email: str, token: str, token_type: str) -> None:
        if token_type == token_types.VERIFICATION:
            url = f"http://{settings.FRONTEND_HOST}:{settings.FRONTEND_PORT}/v/{token}"
            subject = "Verification"
            link_text = "Verify Account"
        elif token_type == token_types.PASSWORD_CHANGE:
            url = f"http://{settings.FRONTEND_HOST}:{settings.FRONTEND_PORT}/r/{token}"
            subject = "Password Change"
            link_text = "Change Password"
        else:
            raise InvalidTokenTypeException()

        message = MessageSchema(
            subject=subject,
            recipients=[email],  
            body=f'<a href="{url}" style="font-size: 16px; font-weight: bold;">{link_text}</a>',
            subtype=MessageType.html  
        )

        await self.fastmail.send_message(message)

    async def send_code_email(self, email: str, otp: str) -> None:
        message = MessageSchema(
            subject="Code",
            recipients=[email],
            body=f"<h1>Your code is {otp}</h1>",
            subtype=MessageType.html
        )
        await self.fastmail.send_message(message)

email_service = EmailService()