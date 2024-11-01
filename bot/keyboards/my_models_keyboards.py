from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from Dataset import Dataset

from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.user_keyboards import empty, back_to_main_menu

add_model = InlineKeyboardButton(text="Загрузить модель", callback_data='add_model')

async def my_models_menu() -> InlineKeyboardMarkup:
    
    kb = InlineKeyboardBuilder()
    my_models = ['1', '2']
    
    if my_models:
        for model in my_models:
            kb.add(InlineKeyboardButton(text=model, callback_data=f'model_launch_{model}'))
        kb.add(add_model)
        kb.add(back_to_main_menu)
    
        return kb.adjust(1).as_markup()
    else:
        kb.add(empty)
        kb.add(add_model)
        kb.add(back_to_main_menu)
        
        return kb.adjust(1).as_markup()