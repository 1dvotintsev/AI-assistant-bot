from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_model import orm_get_user_models

from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.user_keyboards import empty, back_to_main_menu

#add_model = InlineKeyboardButton(text="Загрузить модель", callback_data='add_model') подумать над бизнес логикой надо

async def my_models_menu(session: AsyncSession, user_id: int) -> InlineKeyboardMarkup:
    
    kb = InlineKeyboardBuilder()
    my_models = await orm_get_user_models(session, user_id)
    
    if my_models:
        for model in my_models:
            kb.add(InlineKeyboardButton(text=model, callback_data=f'model_launch_{model}'))
        #kb.add(add_model)
        kb.add(back_to_main_menu)
    
        return kb.adjust(1).as_markup()
    else:
        kb.add(empty)
        #kb.add(add_model)
        kb.add(back_to_main_menu)
        
        return kb.adjust(1).as_markup()