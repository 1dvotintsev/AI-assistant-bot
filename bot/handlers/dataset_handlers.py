from aiogram import F, Router

from User import User

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import CallbackQuery

from bot.keyboards.dataset_keybords import dataset_info


class Form(StatesGroup):
    dataset_name = State()


router = Router()


@router.callback_query(lambda c: c.data.startswith('set_launch'))
async def info(callback: CallbackQuery, state: FSMContext) -> None:
    #сохраняем данные
    dataset = callback.data.split('_')[-1]
    
    await state.update_data(dataset_name = dataset)
    
    await callback.message.edit_text(text = f"{dataset}\nРазмер на: coming soon...\nАвтор: coming soon...\nОписание: coming soon...\nДата загрузки: coming soon...\nСтатус: coming soon...",
                               reply_markup = dataset_info)
    

@router.callback_query(F.data == 'download_dataset')
async def run_model(callback: CallbackQuery, state:FSMContext) -> None:
    # Получаем сохранённые данные
    data = await state.get_data()
    dataset = data.get('model_name')

    await callback.answer()
    
    await callback.message.answer_document() #указать путь по непонятно куда
    
    
@router.callback_query(F.data == 'save_dataset')
async def save_models(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    
    User.save_model(data.get('dataset_name'))
    
    await callback.answer()
    
    
    
    