import os
from config import CONNECTION
from config import DATASET_EXTENSIONS

from aiogram.types import Message

from psycopg import AsyncConnection
import psycopg

class Dataset:
    
    async def download(msg: Message) -> bool:
        try:
            document = msg.document
            mime_type = document.mime_type

            # Проверка MIME-типа
            #if mime_type not in DATASET_EXTENSIONS:
            #    return

            # Получение файла по его file_id
            file_id = document.file_id
            file_info = await msg.bot.get_file(file_id)
            downloaded_file = await msg.bot.download_file(file_info.file_path)

            # Путь для сохранения файла
            file_path = os.path.join('Datasets', file_id)

            # Сохранение файла на сервер
            with open(file_path, 'wb') as new_file:
                new_file.write(downloaded_file.read())
            return True
        except Exception as e:
            print(f"Error: {e}")
    
    
    async def insert_into_db(dataset_id, user_id, name, description, ext, size, status) -> bool:
        try:
            async with await AsyncConnection.connect(CONNECTION) as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO datasets (dataset_id, user_id, name, description, format, size, status, is_public)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
                        (dataset_id, user_id, name, description, ext, size, status, False)
                    )
                    await connection.commit()
                    
                    await cursor.execute(
                        """UPDATE users
                           SET dataset_cnt = dataset_cnt + 1
                           WHERE user_id = %s;
                        """,
                        (user_id,)
                    )
                    await connection.commit()
                    
                    await cursor.execute(
                        """INSERT INTO users_datasets (user_id, dataset_id)
                           VALUES (%s, %s);""",
                        (user_id, dataset_id)
                    )
                    await connection.commit()
                    return True
        except Exception as e:
            print(f"Error: {e}")
    
    
    async def users_datasets(user_id: int) -> list:
        try:
            async with await AsyncConnection.connect(CONNECTION) as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """SELECT d.name
                           FROM datasets d
                           JOIN users_datasets ud ON d.dataset_id = ud.dataset_id
                           WHERE ud.user_id = %s;""",
                        (user_id,)
                    )
                    datasets = await cursor.fetchall()
                    return [dataset[0] for dataset in datasets]  # Возвращаем список названий
        except Exception as e:
            print(f"Error: {e}")
            return []
        
    
    async def dataset_info(dataset_name: str) -> tuple:
        try:
            async with await AsyncConnection.connect(CONNECTION) as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """SELECT d.description, d.format, d.size, d.status, u.username, d.is_public
                           FROM datasets d
                           JOIN users u ON d.user_id = u.user_id
                           WHERE d.name = %s;""",
                        (dataset_name,)
                    )
                    data = await cursor.fetchone()
                    return data
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    
    async def change_public(dataset_name: str) -> bool:
        try:
            async with await AsyncConnection.connect(CONNECTION) as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """UPDATE datasets
                           SET is_public = NOT is_public
                           WHERE name = %s;
                        """,
                        (dataset_name,)
                    )
                    await connection.commit()
                    return True
        except Exception as e:
            print(f"Error: {e}")
            return False
        
    
    async def delete_user_dataset(user_id: int, dataset_name: str) -> bool:
        try:
            async with await AsyncConnection.connect(CONNECTION) as connection:
                async with connection.cursor() as cursor:
                # Получаем dataset_id по dataset_name
                    await cursor.execute(
                        """
                        SELECT dataset_id FROM datasets
                        WHERE name = %s;
                        """,
                        (dataset_name,)
                    )
                    dataset_id = await cursor.fetchone()
                
                    if dataset_id:
                    # Удаляем запись из users_datasets по user_id и dataset_id
                        await cursor.execute(
                            """
                            DELETE FROM users_datasets
                            WHERE user_id = %s AND dataset_id = %s;
                            """,
                            (user_id, dataset_id[0])
                        )
                        await connection.commit()
                        return True
                    else:
                        print("Dataset not found.")
                        return False
        except Exception as e:
            print(f"Error: {e}")
            return False


    async def get_id(dataset_name: str) -> tuple:
        try:
            async with await AsyncConnection.connect(CONNECTION) as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """SELECT dataset_id, format
                           FROM datasets
                           WHERE name = %s;""",
                        (dataset_name,)
                    )
                    data = await cursor.fetchone()
                    return data
        except Exception as e:
            print(f"Error: {e}")
            return None   
        
        
    async def is_saved(dataset_name:str, user_id) -> tuple:
        try:
            async with await AsyncConnection.connect(CONNECTION) as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        SELECT *
                        FROM users_datasets ud
                        JOIN datasets d ON d.dataset_id = ud.dataset_id
                        WHERE ud.user_id = %s AND d.name = %s; 
                        """,
                        (user_id, dataset_name)
                    )
                    data = await cursor.fetchone()
                    return data
        except Exception as e:
            print(f"Error: {e}")
            return None
        
    
    async def save(user_id, dataset_name: str) -> bool:
        print(f"name: {dataset_name}")
        try:
            async with await AsyncConnection.connect(CONNECTION) as connection:
                async with connection.cursor() as cursor:
                # Выполняем запрос для получения dataset_id по имени
                    await cursor.execute(
                        """
                        SELECT dataset_id
                        FROM datasets
                        WHERE name = %s;
                        """,
                        (dataset_name,)
                    )
                    dataset_id = await cursor.fetchone()
                
                # Проверяем, найден ли dataset_id
                    if dataset_id:
                        dataset_id = dataset_id[0]  # dataset_id находится в первой ячейке результата
                    
                    # Выполняем вставку в таблицу users_datasets
                        await cursor.execute(
                            """
                            INSERT INTO users_datasets (user_id, dataset_id)
                            VALUES (%s, %s);
                            """,
                            (user_id, dataset_id)
                        )
                        await connection.commit()
                        print('Insert commit')
                        return True
                    else:
                        print(f"Dataset with name {dataset_name} not found.")
                        return False
        except Exception as e:
            print(f"Error: {e}")
            return False


    
    async def public_datasets() -> list:
        try:
            async with await AsyncConnection.connect(CONNECTION) as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """SELECT name
                           FROM datasets
                           WHERE is_public = true;"""
                    )
                    datasets = await cursor.fetchall()
                    return [dataset[0] for dataset in datasets]  # Возвращаем список названий
        except Exception as e:
            print(f"Error: {e}")
            return []    
    
    
    async def is_owned(dataset_name:str, user_id) -> tuple:
        try:
            async with await AsyncConnection.connect(CONNECTION) as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        SELECT *
                        FROM datasets
                        WHERE user_id = %s AND name = %s; 
                        """,
                        (user_id, dataset_name)
                    )
                    data = await cursor.fetchone()
                    return data
        except Exception as e:
            print(f"Error: {e}")
            return None     
            
