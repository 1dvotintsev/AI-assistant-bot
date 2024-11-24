from sqlalchemy.ext.asyncio import AsyncSession
from models import Users


async def orm_add_user(session: AsyncSession, data:dict):
    obj = Users(
        user_id = data['user_id'],
        username = data['username']
    )
    session.add(obj)
    await session.commit()