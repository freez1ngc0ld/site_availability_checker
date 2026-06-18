from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self, 
        order_by: Any = None, 
        offset: int | None = None, 
        limit: int | None = None,
        between_field: str | None = None,  
        between_start: Any = None,         
        between_end: Any = None,           
        **filters
    ):
        stmt = select(self.model)
        
        if between_field and between_start is not None and between_end is not None:
            if hasattr(self.model, between_field):
                model_field = getattr(self.model, between_field)
                stmt = stmt.where(model_field.between(between_start, between_end))

        for field, value in filters.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)

        if order_by is not None:
            if isinstance(order_by, str):
                if order_by.startswith('-'):
                    field_name = order_by[1:]
                    if hasattr(self.model, field_name):
                        stmt = stmt.order_by(getattr(self.model, field_name).desc())
                else:
                    if hasattr(self.model, order_by):
                        stmt = stmt.order_by(getattr(self.model, order_by).asc())
            else:
                stmt = stmt.order_by(order_by)

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_first(self, **filters):
        stmt = select(self.model)
        for field, value in filters.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.db.execute(stmt)
        return result.scalar()

    async def get_by_pk(self, pk: Any):
        return await self.db.get(self.model, pk)

    async def create(self, **kwargs):
        obj = self.model(**kwargs)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def delete(self, pk: Any) -> bool:
        obj = await self.get_by_pk(pk)
        if obj:
            await self.db.delete(obj)
            await self.db.flush()
            return True
        return False
