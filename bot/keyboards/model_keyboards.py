from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


not_saved_model_info = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Запустить', callback_data='run')],
    [InlineKeyboardButton(text='Сохранить себе', callback_data = 'save')],
    [InlineKeyboardButton(text = 'Назад к моделям', callback_data = 'models_menu')],
    ])

saved_model_info = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Запустить', callback_data='run')],
    [InlineKeyboardButton(text='Модель сохранена', callback_data = '')],
    [InlineKeyboardButton(text = 'Назад к моделям', callback_data = 'models_menu')],
    ])
