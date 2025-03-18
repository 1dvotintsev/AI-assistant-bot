from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import Users, Transactions
from decimal import Decimal


async def orm_add_user(session: AsyncSession, data:dict):
    obj = Users(
        user_id = data['user_id'],
        username = data['username']
    )
    session.add(obj)
    await session.commit()
    
async def orm_update_balance(session: AsyncSession, hash: str, user_id: int, amount: float, transaction_type: str, address: str | None = None):
    if transaction_type not in ("deposit", "withdraw"):
        raise ValueError("Invalid transaction type. Must be 'deposit' or 'withdraw'.")

    async with session.begin():  # Начало транзакции
        # Получаем пользователя
        result = await session.execute(select(Users).where(Users.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found.")

        # Проверка баланса при выводе
        if transaction_type == "withdraw" and user.balance < amount:
            raise ValueError("Insufficient funds.")

        # Обновляем баланс
        new_balance = user.balance + Decimal(amount) if transaction_type == "deposit" else user.balance - Decimal(amount)
        await session.execute(
            update(Users)
            .where(Users.user_id == user_id)
            .values(balance=new_balance)
        )

        # Создаём транзакцию
        transaction = Transactions(
            hash=hash,
            user_id=user_id,
            value=amount,
            type=transaction_type,
            address=address
        )
        session.add(transaction)

    await session.commit()
    return {"user_id": user_id, "new_balance": new_balance, "transaction_id": transaction}