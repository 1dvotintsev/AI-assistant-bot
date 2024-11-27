from aiogram import F, Router

from User import User

from Model import Model

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.types import CallbackQuery, Message

from aiogram.filters import Command

from bot.keyboards.model_keyboards import not_saved_model_info, saved_model_info
from bot.keyboards.user_keyboards import back_to_main_menu_mk

from database.orm_model import orm_get_model_info, orm_model_is_saved, orm_add_model_to_user, orm_delete_model_from_user


router = Router()

@router.message(Command(commands=['stop']))
async def stop_model(msg: Message, state: FSMContext) -> None:
    data = await state.get_data()
    
    if data.get('model_run'):
        # сдесь реально отанавливаем модель
        await state.update_data(model_name = None, model_run = False)
        await msg.answer(text=f"Работа модели {data.get('model_name')} прекращена.")
    else:
        await msg.answer(text="В данный момент времени нет запущенных моделей.")
        


@router.callback_query(lambda c: c.data.startswith('model_launch'))
async def info(callback: CallbackQuery, session: AsyncSession) -> None:
    model = callback.data.split('_')[-1]
    user_id = callback.from_user.id
    
    data = await orm_get_model_info(session, model)
    
    if data:
        await callback.message.edit_text(text = f"Имя: {model}\n\nОписание: {data['description']}\n\nВерсия: {data['version']}\n\nЗагрузил: @{data['username']}",
                               reply_markup = saved_model_info(model) if await orm_model_is_saved(session, user_id, model) else not_saved_model_info(model))
    else:
        await callback.message.edit_text(text = "Что-то пошло не так :(",
                                         reply_markup = back_to_main_menu_mk)
    

@router.callback_query(lambda c: c.data.startswith('run'))
async def run_model(callback: CallbackQuery) -> None:
    model = callback.data.split('_')[-1]

    if model:   #чуть позже добавть реальное подключение к серверу
        await callback.message.edit_text(f"Вы используете модель {model}. Для остановки напишите команду /stop")
    else:
        await callback.message.edit_text("Модель не была выбрана.")
    
    await callback.answer()
    
    
@router.callback_query(lambda c: c.data.startswith('save'))
async def save_models(callback: CallbackQuery, session: AsyncSession) -> None:
    model = callback.data.split('_')[-1]
    user_id = callback.from_user.id
    try:
        await orm_add_model_to_user(session, model, user_id)
        await callback.message.edit_text(text="Модель была сохранена",
                                         reply_markup=back_to_main_menu_mk)
    except Exception as e:
        print(e)
        await callback.message.edit_text(text="Произошла ошибка :(",
                                         reply_markup=back_to_main_menu_mk)
    
    await callback.answer()
    

@router.callback_query(lambda c: c.data.startswith('rm_model'))
async def save_models(callback: CallbackQuery, session: AsyncSession) -> None:
    model = callback.data.split('_')[-1]
    user_id = callback.from_user.id
    
    try:
        await orm_delete_model_from_user(session, model, user_id)
        await callback.message.edit_text(text="Модель была удалена",
                                         reply_markup=back_to_main_menu_mk)
    except Exception as e:
        print(e)
        await callback.message.edit_text(text="Произошла ошибка :(",
                                         reply_markup=back_to_main_menu_mk)
    
    await callback.answer()    
    
    