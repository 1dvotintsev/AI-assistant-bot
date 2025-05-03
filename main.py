import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import TOKEN, GIGACHAT_CLIENT_ID, GIGACHAT_CLIENT_SECRET
from bot.middlewares.session import DataBaseSession
from database.engine import async_session

from bot.handlers.user_handlers        import router as user_router
from bot.handlers.models_handlers      import router as model_router
from bot.handlers.dataset_handlers     import router as dataset_router
from bot.handlers.my_models_handler    import router as my_models_router
from bot.handlers.my_datasets_handler  import router as my_datasets_router
from bot.handlers.balance_handlers     import router as balance_router
from bot.handlers.orders_handlers      import router as order_router


dp = Dispatcher()


async def main() -> None:
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    from bot.services.gigachat_client import GigaChatClient

    gigachat = GigaChatClient(          
        client_id=GIGACHAT_CLIENT_ID,
        client_secret=GIGACHAT_CLIENT_SECRET,
    )
    bot.gigachat = gigachat

    dp.update.middleware(DataBaseSession(session_pool=async_session))

    dp.include_router(user_router)
    dp.include_router(model_router)
    dp.include_router(dataset_router)
    dp.include_router(my_models_router)
    dp.include_router(my_datasets_router)
    dp.include_router(balance_router)
    dp.include_router(order_router)

    async def on_shutdown() -> None:
        await bot.gigachat.close()          # закрываем свою aiohttp-сессию
        await bot.session.close()           # закрываем сессию Telegram-бота

    await dp.start_polling(bot, shutdown=on_shutdown)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass