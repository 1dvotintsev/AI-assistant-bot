from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Dataset import Dataset

from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.fsm.context import FSMContext


async def dataset_settings(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    user_id = data.get('userid')
    kb = InlineKeyboardBuilder()
    dataset = data.get('dataset_name')
    print(dataset)
    saved = await Dataset.is_saved(dataset, user_id)
    
    if not saved:
        kb.add(InlineKeyboardButton(text="Сохранить себе", callback_data=f'save_dataset_{dataset}'))
        kb.add(InlineKeyboardButton(text = 'Назад к датасетам', callback_data = 'datasets_menu'))
    
        return kb.adjust(1).as_markup()
    else:
        kb.add(InlineKeyboardButton(text="Удалить", callback_data=f'dataset_delete_{dataset}'))
        kb.add(InlineKeyboardButton(text = 'Назад к датасетам', callback_data = 'datasets_menu'))
        
        return kb.adjust(1).as_markup()
