from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Models
from sqlalchemy import select


async def orm_get_models(session: AsyncSession) -> list[str]:
    query = select(Models.model_name)
    result = await session.execute(query)
    return result.scalars().all()
