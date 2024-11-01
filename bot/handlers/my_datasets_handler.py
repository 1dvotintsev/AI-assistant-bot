from config import DATASET_EXTENSIONS

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import CallbackQuery, Message, ContentType

from aiogram.filters import Command

from Dataset import Dataset

from bot.keyboards.my_datasets_keybords import my_datasets_menu

from bot.keyboards.user_keyboards import main_menu


class UploadDataset(StatesGroup):
    adding = State()
    dataset_name = State()
    dataset_description = State()
    dataset_acces = State()
    

router = Router()
    

@router.callback_query(F.data == 'user_datasets')
async def run_model(callback: CallbackQuery, state:FSMContext) -> None:
    await callback.answer()
    await state.update_data(user_id = callback.from_user.id)
    await callback.message.edit_text(text="Ваши сохраненные модели:",
                                     reply_markup= await my_datasets_menu(state))


@router.callback_query(F.data == 'add_dataset')
async def add_model(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(UploadDataset.adding)
    await callback.message.edit_text(text=f"Отправьте файл с датасетом, он должен быть одно из этих форматов: {DATASET_EXTENSIONS}")


@router.message(Command(commands = ['drop_form']))
async def drop_form(msg: Message, state: FSMContext) -> None:
    await state.clear()
    
    
@router.message(UploadDataset.adding)
async def get_file(msg: Message, state:FSMContext) -> None:
    if await Dataset.download(msg):
        await state.update_data(dataset_id = msg.document.file_id)
        await msg.answer(text="Как назовем датасет?")
        await state.set_state(UploadDataset.dataset_name)
    else:
        await msg.answer(text="Нужно отправить определенный файл, попробуйте еще раз.")


@router.message(UploadDataset.dataset_name)
async def get_name(msg: Message, state: FSMContext):
    await state.update_data(dataset_name = msg.text)
    await msg.answer(text="Напишите описание датасета:")
    await state.set_state(UploadDataset.dataset_description)
   

@router.message(UploadDataset.dataset_description)
async def get_description(msg: Message, state: FSMContext) -> None:
    data = await state.get_data()
    dataset_id = data.get('dataset_id')
    name = data.get('dataset_name')
    user_id = data.get('user_id')
    description = msg.text
    await msg.answer(text= "Все прошло успешно" if await Dataset.insert_into_db(dataset_id, user_id, name, description) else "Что-то пошло не так",
                     reply_markup=main_menu)
    await state.clear()
   
    