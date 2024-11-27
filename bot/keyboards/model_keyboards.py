from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def not_saved_model_info(model_name: str) -> InlineKeyboardMarkup:
    model_info = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Запустить', callback_data=f'run_{model_name}')],
        [InlineKeyboardButton(text='Сохранить себе', callback_data = f'save_{model_name}')],
        [InlineKeyboardButton(text = 'Назад к моделям', callback_data = 'models_menu')],
        ])
    return model_info

def saved_model_info(model_name: str) -> InlineKeyboardMarkup:
    model_info = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Запустить', callback_data=f'run_{model_name}')],
        [InlineKeyboardButton(text='Удалить модель', callback_data = f'rm_model_{model_name}')],
        [InlineKeyboardButton(text = 'Назад к моделям', callback_data = 'models_menu')],
        ])
    return model_info
