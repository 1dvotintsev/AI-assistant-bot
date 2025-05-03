from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import CallbackQuery, Message

from aiogram.filters import Command

from Model import Model

from bot.keyboards.my_models_keyboards import my_models_menu
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.user_keyboards import main_menu


class UploadModel(StatesGroup):
    adding = State()
    model_name = State()
    model_description = State()
    model_version = State()
    

router = Router()
    

@router.callback_query(F.data == 'user_models')
async def run_model(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    await callback.message.edit_text(text="Ваши сохраненные модели:",
                                     reply_markup= await my_models_menu(session, callback.from_user.id))


@router.message(Command(commands = ['drop_form']))
async def drop_form(msg: Message, state: FSMContext) -> None:
    await state.clear()
   

   
    