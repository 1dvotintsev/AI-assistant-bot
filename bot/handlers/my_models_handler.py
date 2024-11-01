from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import CallbackQuery, Message, ContentType

from aiogram.filters import Command

from Model import Model

from bot.keyboards.my_models_keyboards import my_models_menu

from bot.keyboards.user_keyboards import main_menu


class UploadModel(StatesGroup):
    start = State()
    adding = State()
    model_name = State()
    model_description = State()
    model_version = State()
    

router = Router()
    

@router.callback_query(F.data == 'user_models')
async def run_model(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(UploadModel.start)
    await state.update_data(user_id = callback.from_user.id)
    await callback.message.edit_text(text="Ваши сохраненные модели:",
                                     reply_markup= await my_models_menu())


@router.callback_query(F.data == 'add_model')
async def add_model(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(UploadModel.adding)
    await callback.message.edit_text(text="Отправьте файл с обученной моделью в ответ на это сообщение.")


@router.message(Command(commands = ['drop_form']))
async def drop_form(msg: Message, state: FSMContext) -> None:
    await state.clear()
    
    
@router.message(UploadModel.adding)
async def get_file(msg: Message, state:FSMContext) -> None:
    if Model.is_upload(msg):
        await msg.answer(text="Как назовем модель?")
        await state.set_state(UploadModel.model_name)
    else:
        await msg.answer(text="Нужно отправить определенный файл, попробуйте еще раз.")


@router.message(UploadModel.model_name)
async def get_name(msg: Message, state: FSMContext):
    await state.update_data(model_name = msg.text)
    await msg.answer(text="Напишите описание модели:")
    await state.set_state(UploadModel.model_description)
   

@router.message(UploadModel.model_description)
async def get_description(msg: Message, state: FSMContext) -> None:
    data = await state.get_data()
    file = ''
    name = data.get('model_name')
    description = msg.text
    await msg.answer(text= "Все прошло успешно" if Model.is_done(file, name, description) else "Что-то пошло не так",
                     reply_markup=main_menu)
    await state.clear()
   
    