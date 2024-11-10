from config import DATASET_EXTENSIONS
import os
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import CallbackQuery, Message, ContentType

from aiogram.filters import Command

from Dataset import Dataset

from bot.keyboards.my_datasets_keybords import my_datasets_menu, my_datasets_settings, status

from bot.keyboards.user_keyboards import main_menu


class UploadDataset(StatesGroup):
    adding = State()
    dataset_name = State()
    dataset_description = State()
    dataset_acces = State()
    dataset_status = State()
    

router = Router()
    

@router.callback_query(F.data == 'user_datasets')
async def run_model(callback: CallbackQuery, state:FSMContext) -> None:
    await callback.answer()
    await state.update_data(user_id = callback.from_user.id)
    await callback.message.edit_text(text="Ваши сохраненные датасеты:",
                                     reply_markup= await my_datasets_menu(state))
    

@router.callback_query(lambda c: c.data.startswith('dataset_launch'))
async def info(callback: CallbackQuery, state: FSMContext) -> None:
    #сохраняем данные
    dataset_name = callback.data.split('_')[-1]
    data = await Dataset.dataset_info(dataset_name)
    
    if data:
        await state.update_data(public = data[-1])
        await state.update_data(dataset_name_set = dataset_name)
        await state.update_data(userid_myset = callback.from_user.id)
        await callback.message.edit_text(text = f"{dataset_name}\nОписание: {data[0]}\nФормат: {data[1]}\nРазмер: {data[2]}\nСтатус: {data[3]}\nАвтор @{data[4]}",
                                reply_markup = await my_datasets_settings(state))
    else:
        await callback.message.answer(text="Что-то пожно не так, похоже данные повреждены!")
    


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
        # Получаем файл из сообщения
        file = msg.document
        file_extension = file.file_name.split('.')[-1] if '.' in file.file_name else None
        file_size = file.file_size
        await state.update_data(dataset_id = msg.document.file_id)
        await state.update_data(dataset_ext = file_extension)
        await state.update_data(dataset_size = file_size)
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
async def get_status(msg: Message, state: FSMContext) -> None:
    await state.update_data(description = msg.text)
    await msg.answer(text="Выберете статус готовности датасета:",
                     reply_markup=status)
    await state.set_state(UploadDataset.dataset_status)


@router.callback_query(F.data == 'done')
async def get_description(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    dataset_id = data.get('dataset_id')
    name = data.get('dataset_name')
    user_id = data.get('user_id')
    dataset_ext = data.get('dataset_ext')
    size = data.get('dataset_size')
    description = data.get('description')
    await callback.message.answer(text= "Все прошло успешно" if await Dataset.insert_into_db(dataset_id, user_id, name, description, dataset_ext, size, 'done') else "Что-то пошло не так",
                     reply_markup=main_menu)
    await state.clear()
    
    
@router.callback_query(F.data == 'notdone')
async def get_description(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    dataset_id = data.get('dataset_id')
    name = data.get('dataset_name')
    user_id = data.get('user_id')
    dataset_ext = data.get('dataset_ext')
    size = data.get('dataset_size')
    description = data.get('description')
    await callback.message.answer(text= "Все прошло успешно" if await Dataset.insert_into_db(dataset_id, user_id, name, description, dataset_ext, size, 'not done') else "Что-то пошло не так",
                     reply_markup=main_menu)
    await state.clear()
    
    
@router.callback_query(lambda c: c.data.startswith('change_public'))
async def info(callback: CallbackQuery, state: FSMContext) -> None:
    dataset_name = callback.data.split('_')[-1]
    
    if await Dataset.change_public(dataset_name):
        await callback.message.edit_text(text = "Изменение произошло успешно!",
                                reply_markup = main_menu)
    else:
        await callback.message.answer(text="Что-то пожно не так, похоже данные повреждены!",
                                      reply_markup= main_menu)
   

@router.callback_query(lambda c: c.data.startswith('dataset_delete'))
async def info(callback: CallbackQuery, state: FSMContext) -> None:
    dataset_name = callback.data.split('_')[-1]
    
    if await Dataset.delete_user_dataset(callback.from_user.id, dataset_name):
        await callback.message.edit_text(text = "Удаление произошло успешно!",
                                reply_markup = main_menu)
    else:
        await callback.message.answer(text="Что-то пожно не так, похоже данные повреждены!",
                                      reply_markup= main_menu)
        
        
from aiogram.types import FSInputFile

@router.callback_query(F.data == 'download')
async def download(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    dataset_name = data.get('dataset_name_set')
    dataset_id, format = map(str, await Dataset.get_id(dataset_name))

    if dataset_id:
        file_name = f"{dataset_id}"
        file_path = os.path.join('Datasets', file_name)

        # Проверка, существует ли файл
        if os.path.exists(file_path):
            await callback.bot.send_document(chat_id=callback.from_user.id, document=FSInputFile(file_path, filename=f'{dataset_name}.{format}'))
        else:
            await callback.message.answer(f"Файл {file_path} не найден.")
    else:
        await callback.message.answer("Файл вообще не найден.")
