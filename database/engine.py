from config import DB_ORM

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


engine = create_async_engine(DB_ORM, echo=True)

async_session = sessionmaker(
    engine, 
    expire_on_commit=False, 
    class_=AsyncSession
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
