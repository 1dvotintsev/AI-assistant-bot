from aiogram import F, Router

from User import User

from Model import Model

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import CallbackQuery, Message

from aiogram.filters import Command

from bot.keyboards.model_keyboards import not_saved_model_info, saved_model_info


class Form(StatesGroup):
    model_name = State()
    model_run = State()
    is_add = State()


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
async def info(callback: CallbackQuery, state: FSMContext) -> None:
    #сохраняем данные
    model = callback.data.split('_')[-1]
    
    await state.update_data(model_name = model)
    
    await callback.message.edit_text(text = f"{model}\nОбучено на: coming soon...\nАвтор: coming soon...\nОписание: coming soon...\nДата загрузки: coming soon...\nверсия: coming soon...",
                               reply_markup = saved_model_info if Model.is_saved(user_id=callback.from_user.id, model_name=model) else not_saved_model_info)
    

@router.callback_query(F.data == 'run')
async def run_model(callback: CallbackQuery, state:FSMContext) -> None:
    # Получаем сохранённые данные
    data = await state.get_data()
    await state.update_data(model_run = True)
    model_id = data.get('model_name')

    if model_id:
        await callback.message.edit_text(f"Вы используете модель {model_id}. Для остановки напишите команду /stop")
    else:
        await callback.message.edit_text("Модель не была выбрана.")
    
    await callback.answer()
    
    
@router.callback_query(F.data == 'save')
async def save_models(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    
    User.save_model(data.get('model_name'))
    print('OK')
    
    await callback.answer()
    
    
    
    