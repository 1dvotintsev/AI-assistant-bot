import asyncio

from config import TOKEN

from aiogram import Bot, Dispatcher

from bot.middlewares.session import DataBaseSession
from database.engine import async_session

from bot.handlers.user_handlers import router as user_router
from bot.handlers.models_handlers import router as model_router
from bot.handlers.dataset_handlers import router as dataset_router
from bot.handlers.my_models_handler import router as my_models_router
from bot.handlers.my_datasets_handler import router as my_datasets_router
from bot.handlers.balance_handlers import router as balance_router


bot = Bot(token = TOKEN)
dp = Dispatcher()


async def main() -> None:
    dp.include_router(user_router)
    dp.include_router(model_router)
    dp.include_router(dataset_router)
    dp.include_router(my_models_router)
    dp.include_router(my_datasets_router)
    dp.include_router(balance_router)
    dp.update.middleware(DataBaseSession(session_pool=async_session))
    await dp.start_polling(bot)
    

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except:
        pass