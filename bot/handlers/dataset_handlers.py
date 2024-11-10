from aiogram import F, Router

from User import User
from Dataset import Dataset

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import CallbackQuery

from bot.keyboards.dataset_keybords import dataset_settings
from bot.keyboards.user_keyboards import main_menu


class Form(StatesGroup):
    dataset_name = State()


router = Router()


@router.callback_query(lambda c: c.data.startswith('set_launch'))
async def info(callback: CallbackQuery, state: FSMContext) -> None:
    #сохраняем данные
    dataset_name = callback.data.split('_')[-1]
    data = await Dataset.dataset_info(dataset_name)
    
    if data:
        await state.update_data(userid = callback.from_user.id)
        await state.update_data(dataset_name = dataset_name)
        await callback.message.edit_text(text = f"{dataset_name}\nОписание: {data[0]}\nФормат: {data[1]}\nРазмер: {data[2]}\nСтатус: {data[3]}\nАвтор @{data[4]}",
                                reply_markup = await dataset_settings(state))
    else:
        await callback.message.answer(text="Что-то пожно не так, похоже данные повреждены!")
    

@router.callback_query(F.data == 'download_dataset')
async def run_model(callback: CallbackQuery, state:FSMContext) -> None:
    # Получаем сохранённые данные
    data = await state.get_data()
    dataset = data.get('model_name')

    await callback.answer()
    
    await callback.message.answer_document() #указать путь по непонятно куда
    
    
@router.callback_query(lambda c: c.data.startswith('save_dataset'))
async def save(callback: CallbackQuery, state: FSMContext) -> None:
    dataset_name = callback.data.split('_')[-1]
    data = await Dataset.save(callback.from_user.id, dataset_name)
    
    if data:    
        await callback.message.edit_text(text = f"Сохранение произошло успешно!",
                                reply_markup = main_menu)
        await state.clear()
    else:
        await callback.message.answer(text="Что-то пожно не так, похоже данные повреждены!")
        
    await callback.answer()
    
    
    
    