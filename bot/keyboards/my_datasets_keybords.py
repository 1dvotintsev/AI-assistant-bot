from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Dataset import Dataset

from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.fsm.context import FSMContext

from bot.keyboards.user_keyboards import empty, back_to_main_menu

add_dataset = InlineKeyboardButton(text="Загрузить датасет", callback_data='add_dataset')

back_to_my_datasets = InlineKeyboardButton(text='Назад', callback_data='user_datasets')

status = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Размечен', callback_data='done')],
    [InlineKeyboardButton(text='Не размечен', callback_data='notdone')],
])

async def my_datasets_menu(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    user_id = data.get('user_id')
    kb = InlineKeyboardBuilder()
    my_datasets = await Dataset.users_datasets(user_id)
    
    if my_datasets:
        for dataset in my_datasets:
            kb.add(InlineKeyboardButton(text=dataset, callback_data=f'dataset_launch_{dataset}'))
        kb.add(add_dataset)
        kb.add(back_to_main_menu)
    
        return kb.adjust(1).as_markup()
    else:
        kb.add(empty)
        kb.add(add_dataset)
        kb.add(back_to_main_menu)
        
        return kb.adjust(1).as_markup()
    
    
async def my_datasets_settings(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    public = data.get('public')
    kb = InlineKeyboardBuilder()
    dataset = data.get('dataset_name_set')
    user_id = data.get('userid_myset')
    owned = await Dataset.is_owned(dataset, user_id)
    
    if public:
        kb.add(InlineKeyboardButton(text="Скачать", callback_data='download'))
        if owned:
            kb.add(InlineKeyboardButton(text="Сделать приватным", callback_data=f'change_public_{dataset}'))
        kb.add(InlineKeyboardButton(text="Удалить", callback_data=f'dataset_delete_{dataset}'))
        kb.add(back_to_my_datasets)
    
        return kb.adjust(1).as_markup()
    else:
        kb.add(InlineKeyboardButton(text="Скачать", callback_data='download'))
        if owned:
            kb.add(InlineKeyboardButton(text="Сделать публичным", callback_data=f'change_public_{dataset}'))
        kb.add(InlineKeyboardButton(text="Удалить", callback_data=f'dataset_delete_{dataset}'))
        kb.add(back_to_my_datasets)
        
        return kb.adjust(1).as_markup()