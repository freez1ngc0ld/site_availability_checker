from src.core.base.schema import BaseSchema
from datetime import datetime


class SiteCheckerSchema(BaseSchema):
    id: str
    site_url: str
    created_at: datetime


class CheckerLogSchema(BaseSchema):
    id: str
    status_code: int
    response_time_ms: int
    created_at: datetime

