from dataclasses import dataclass


@dataclass(frozen=True)
class TokenTypes:
    AUTHORIZATION = 'authorization'
    VERIFICATION = 'verification'
    PASSWORD_CHANGE = 'password_change'
    ACCOUNT_DELETE = 'account_delete'
    