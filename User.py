from config import CONNECTION
import sys
import asyncio
from psycopg import AsyncConnection
import psycopg

# Устанавливаем политику событий для совместимости с Psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Ваш класс User с асинхронными методами
class User:
    
    
    async def reg_user(user_id, user_name, balance):
        try:
            async with await AsyncConnection.connect(CONNECTION) as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO users (user_id, username, balance) 
                        VALUES (%s, %s, %s)""",
                        (user_id, user_name, balance)
                    )
                    await connection.commit()
                    print(f"User {user_name} registered successfully.")
        except Exception as e:
            print(f"Error: {e}")


    async def is_exist(user_id: int) -> bool:
        try:
            async with await AsyncConnection.connect(CONNECTION) as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """SELECT EXISTS(SELECT 1 FROM users WHERE user_id = %s)""",
                        (user_id,)
                    )
                    exists = await cursor.fetchone()
                    return exists[0]  # Возвращаем True или False
        except Exception as e:
            print(f"Error: {e}")
            return False  # В случае ошибки возвращаем False
    
    
    def save_model(model_name: str) -> None:
        pass