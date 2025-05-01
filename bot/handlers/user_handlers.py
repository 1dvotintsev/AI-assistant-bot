from aiogram import F, Router

from User import User

from aiogram.filters import CommandStart

from aiogram.types import Message, CallbackQuery

from bot.keyboards.user_keyboards import main_menu, models_menu, datasets_menu, orders_menu

from bot.keyboards.balance_keyboards import balance_operations

from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession


router = Router()


@router.message(CommandStart())
async def cmd_start(msg: Message, state:FSMContext) -> None:
    await state.clear()
    if not await User.is_exist(msg.from_user.id):
        
        await User.reg_user(msg.from_user.id, msg.from_user.username)
        
        await msg.answer(f"Привет, {msg.from_user.first_name}, добро пожаловать в сообщество AI assistant. Вот твой личный кабинет", 
                        reply_markup=main_menu)
    else:
        data = await User.get_user_info(msg.from_user.id)
        await msg.answer(text=f"Информация о профиле\nИмя: {msg.from_user.username}\nЗагружено датасетов: {data[0]}\nЗагружено моделей: {data[1]}\nБаланс: {data[2]}",
                         reply_markup=main_menu)



@router.callback_query(F.data == 'main')
async def cmd_start(callback: CallbackQuery, state:FSMContext) -> None:
    await state.clear()
    await callback.answer()
    data = await User.get_user_info(callback.from_user.id)
    await callback.message.edit_text(text=f"Информация о профиле\nИмя: {callback.from_user.username}\nЗагружено датасетов: {data[0]}\nЗагружено моделей: {data[1]}\nБаланс: {data[2]}",
                         reply_markup=main_menu)
        

@router.callback_query(F.data == 'models_menu')
async def all_models(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    await callback.message.edit_text(text="Для подробной информации выберете одну из моделей",
                                  reply_markup=await models_menu(session))


@router.callback_query(F.data == 'datasets_menu')
async def all_datasets(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(text="Для подробной информации выберете один из датасетов",
                                  reply_markup=await datasets_menu())
    
    
#@router.callback_query(F.data == 'orders_menu')
#async def all_orders(callback: CallbackQuery) -> None:
#    await callback.answer()
#    await callback.message.edit_text(text="Выберете один из датасетов для разметки",
#                                  reply_markup=await orders_menu())
    
    
@router.callback_query(F.data == 'balance')
async def all_datasets(callback: CallbackQuery) -> None:
    await callback.answer()
    data = await User.get_user_info(callback.from_user.id)
    await callback.message.edit_text(text=f"На вашем балансе находится {data[2]} TON",
                                  reply_markup=balance_operations())