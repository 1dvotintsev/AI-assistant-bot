from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


dataset_info = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Скачать', callback_data='download_dataset')],
    [InlineKeyboardButton(text='Сохранить себе', callback_data = 'save_dataset')],
    [InlineKeyboardButton(text = 'Назад к датасетам', callback_data = 'datasets_menu')],
    ])
