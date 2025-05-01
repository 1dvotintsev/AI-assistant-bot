from config import DATASET_EXTENSIONS
import os
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

from Dataset import Dataset
from decimal import Decimal, InvalidOperation

from bot.keyboards.my_datasets_keybords import my_datasets_menu, my_datasets_settings, status, need_markup

from bot.keyboards.user_keyboards import main_menu


class UploadDataset(StatesGroup):
    adding              = State()   # файл
    need_labeling       = State()   # да/нет
    dataset_name        = State()
    dataset_description = State()
    label_positive      = State()
    label_negative      = State()
    reward_pool         = State()
    confirm             = State()
    

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
async def get_file(msg: Message, state: FSMContext):
    if not await Dataset.download(msg):
        await msg.answer("Пришли CSV-файл.")
        return

    ok, rows = await Dataset.verify_csv(f"Datasets/{msg.document.file_id}")
    if not ok:
        await msg.answer("CSV должен содержать ровно одну колонку 🤷‍♂️")
        return

    await state.update_data(
        dataset_id = msg.document.file_id,
        dataset_size = msg.document.file_size,
        csv_rows = rows
    )
    await msg.answer("Требуется ли разметка датасета?", reply_markup=need_markup)
    await state.set_state(UploadDataset.need_labeling)


@router.callback_query(F.data == 'labeling_no', UploadDataset.need_labeling)
async def just_store(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # …тут оставь старый сценарий (name → desc → статус) …
    await state.set_state(UploadDataset.dataset_name)
    

@router.callback_query(F.data == 'labeling_yes', UploadDataset.need_labeling)
async def labeling_flow(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Придумай название датасета:")
    await state.set_state(UploadDataset.dataset_name)
    

@router.message(UploadDataset.dataset_name)
async def get_name(msg: Message, state: FSMContext):
    await state.update_data(dataset_name = msg.text)
    await msg.answer(text="Напишите описание датасета:")
    await state.set_state(UploadDataset.dataset_description)


@router.message(UploadDataset.dataset_description)
async def ask_pos_label(msg: Message, state: FSMContext):
    await state.update_data(description = msg.text)
    await msg.answer("Название *положительного* класса (пример: `spam`):")
    await state.set_state(UploadDataset.label_positive)
    

@router.message(UploadDataset.label_positive)
async def ask_neg_label(msg: Message, state: FSMContext):
    await state.update_data(label_positive = msg.text)
    await msg.answer("Название *отрицательного* класса (пример: `ham`):")
    await state.set_state(UploadDataset.label_negative)
    

@router.message(UploadDataset.label_negative)
async def ask_pool(msg: Message, state: FSMContext):
    await state.update_data(label_negative = msg.text)
    await msg.answer("Сколько выделяем на вознаграждения? (число в TON):")
    await state.set_state(UploadDataset.reward_pool)
    

@router.message(UploadDataset.reward_pool)
async def confirm_info(msg: Message, state: FSMContext):
    try:
        pool = Decimal(msg.text)
    except InvalidOperation:
        return await msg.answer("Нужно число. Попробуй еще.")

    data = await state.update_data(pool = pool)

    text = (f"📦 *{data['dataset_name']}*\n"
            f"Строк: {data['csv_rows']}\n"
            f"Классы: {data['label_positive']} / {data['label_negative']}\n"
            f"Пул наград: {pool} TON\n\n"
            "Подтверждаем загрузку?")
    kb = InlineKeyboardBuilder() \
            .button(text="🚀 Запустить", callback_data="create_job") \
            .button(text="❌ Отмена", callback_data="cancel").as_markup()
    await msg.answer(text, reply_markup=kb, parse_mode='Markdown')
    await state.set_state(UploadDataset.confirm)


@router.callback_query(F.data == 'create_job', UploadDataset.confirm)
async def finish_create(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    data = await state.get_data()

    ok = await Dataset.create_labeling_job(
        session=session,
        user_id = callback.from_user.id,
        name = data['dataset_name'],
        description = data['description'],
        csv_path = f"Datasets/{data['dataset_id']}",
        file_id = data['dataset_id'],
        pos_label = data['label_positive'],
        neg_label = data['label_negative'],
        annotations_per_task = 3,
        pool_amount = data['pool']
    )

    if ok:
        await callback.message.edit_text("✅ Датасет принят и отправлен на разметку!")
    else:
        await callback.message.edit_text("❌ Не хватает средств на балансе.")

    await state.clear()


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
