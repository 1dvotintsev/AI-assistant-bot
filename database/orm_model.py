from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Models, UsersModels, Users
from sqlalchemy import select, join, delete

async def orm_get_models(session: AsyncSession) -> list[str]:
    query = select(Models.model_name)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_model_info(session: AsyncSession, model_name: str) -> dict:
    query = (
        select(
            Models.model_name,
            Models.description,
            Models.version,
            Users.username
        )
        .join(Users, Models.user_id == Users.user_id)
        .where(Models.model_name == model_name)
    )
    
    result = await session.execute(query)
    row = result.first()
    
    if row:
        return {
            "model_name": row.model_name,
            "description": row.description,
            "version": row.version,
            "username": row.username
        }
    
    return None


async def orm_model_is_saved(session: AsyncSession, user_id: int, model_name: str) -> bool:
    query = select(1).where(
        UsersModels.user_id == user_id,
        UsersModels.model_name == model_name
    )
    
    result = await session.execute(query)
    
    return result.scalar() is not None


async def orm_get_user_models(session: AsyncSession, user_id: int) -> list[str] | None:
    try:
        query = select(UsersModels.model_name).where(UsersModels.user_id == user_id)
        result = await session.execute(query)
    except Exception as e:
        print(e)
        result = None
        
    return result.scalars().all()

async def orm_add_model_to_user(session: AsyncSession, model_name: str, user_id: int) -> None:
    obj = UsersModels(model_name=model_name, user_id=user_id)
    session.add(obj)
    await session.commit()


async def orm_delete_model_from_user(session: AsyncSession, model_name: str, user_id: int) -> None:
    query = delete(UsersModels).where(
        UsersModels.model_name == model_name,
        UsersModels.user_id == user_id
    )   
    await session.execute(query)
    await session.commit()