from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from Dataset import Dataset
from database.orm_model import orm_get_models

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Все модели", callback_data='models_menu')],
    [InlineKeyboardButton(text="Все датасеты", callback_data='datasets_menu')],
    [InlineKeyboardButton(text="Доступные заказы", callback_data='orders_menu')],
    [InlineKeyboardButton(text="Детали баланса", callback_data='balance')],
    [InlineKeyboardButton(text="Мои модели", callback_data='user_models'), InlineKeyboardButton(text="Мои датасеты", callback_data='user_datasets')],   
])

empty = InlineKeyboardButton(text="Данных пока нет", callback_data='empty')

back_to_main_menu = InlineKeyboardButton(text='Назад', callback_data='main' )

back_to_main_menu_mk = InlineKeyboardMarkup(inline_keyboard=[
    [back_to_main_menu],
])

async def models_menu(session: AsyncSession) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    models = await orm_get_models(session)
    
    if models:
        for model in models:
            kb.add(InlineKeyboardButton(text=model, callback_data=f'model_launch_{model}'))       
        kb.add(back_to_main_menu)
    
        return kb.adjust(1).as_markup()
    else:
        kb.add(empty)
        kb.add(back_to_main_menu)
        
        return kb.adjust(1).as_markup()
    

async def datasets_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    public_datasets = await Dataset.public_datasets()
    
    if public_datasets:
        for dataset in public_datasets:
            kb.add(InlineKeyboardButton(text=dataset, callback_data=f'set_launch_{dataset}'))
        kb.add(back_to_main_menu)
    
        return kb.adjust(1).as_markup()
    else:
        kb.add(empty)
        kb.add(back_to_main_menu)
        
        return kb.adjust(1).as_markup()
    
    
async def orders_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    orders = ['order1', 'order2']
    
    if orders:
        for order in orders:
            kb.add(InlineKeyboardButton(text=order, callback_data='order_launch'))
        kb.add(back_to_main_menu)
    
        return kb.adjust(1).as_markup()
    else:
        kb.add(empty)
        kb.add(back_to_main_menu)
        
        return kb.adjust(1).as_markup()
    