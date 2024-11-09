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
                    await connection.commit()  # Не забудь зафиксировать изменения
                    
                    await cursor.execute(
                        """INSERT INTO users_datasets (user_id, dataset_id)
                           VALUES (%s, %s);""",
                        (user_id, dataset_id)
                    )
                    await connection.commit()  # Не забудь зафиксировать изменения
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
