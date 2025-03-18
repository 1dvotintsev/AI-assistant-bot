from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.user_keyboards import back_to_main_menu

def balance_operations() -> InlineKeyboardMarkup:
    balance_info = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Пополнить', callback_data=f'deposit')],
        [InlineKeyboardButton(text='Вывести', callback_data = f'withdraw')],
        [back_to_main_menu]
        ])
    return balance_info

submit_mk = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Подтвердить", callback_data='submit'), InlineKeyboardButton(text="Изменить адрес", callback_data='reject')]
])