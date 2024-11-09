from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Dataset import Dataset

from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.fsm.context import FSMContext

from bot.keyboards.user_keyboards import empty, back_to_main_menu

add_dataset = InlineKeyboardButton(text="Загрузить датасет", callback_data='add_dataset')

status = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Размечен', callback_data='done')],
    [InlineKeyboardButton(text='Не размечен', callback_data='notdone')],
])

async def my_datasets_menu(state:FSMContext) -> InlineKeyboardMarkup:
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