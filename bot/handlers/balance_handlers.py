from config import TC, IS_TESTNET, MAIN_ADRESS
import os
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from User import User
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.types import CallbackQuery, Message, ContentType

from aiogram.filters import Command

from Dataset import Dataset

from bot.keyboards.my_datasets_keybords import my_datasets_menu, my_datasets_settings, status

from bot.keyboards.user_keyboards import main_menu, back_to_main_menu_mk

from bot.services.transactions import TonWalletSession

from bot.keyboards.balance_keyboards import submit_mk
    

class WithdrawInfo(StatesGroup):
    ask_amount = State()
    ask_adress = State()


router = Router()
    

@router.callback_query(F.data == 'deposit')
async def deposit(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    
    deposit = TonWalletSession(TC, IS_TESTNET, MAIN_ADRESS)
    wallet = deposit.wallet
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    bot = callback.bot
    
    await callback.message.edit_text(
        text=f"Для пополнения баланса пополните в течение 15 минут кошелек:\n{wallet.address.to_str()}",
        reply_markup=back_to_main_menu_mk
    )
    
    await deposit.wait_for_deposit(bot, chat_id, user_id, session)
    
    
    
@router.callback_query(F.data == 'withdraw')
async def withdraw(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    
    await callback.message.edit_text(
        text=f"Введите количество TON для вывода",
        reply_markup=back_to_main_menu_mk
    )
    
    await state.set_state(WithdrawInfo.ask_amount)
    
    
@router.message(WithdrawInfo.ask_amount)
async def ask_withdraw_amount(msg: Message, state: FSMContext) -> None:
    data = await User.get_user_info(msg.from_user.id)  # Получаем баланс пользователя
    balance = data[2]
    try:
        amount = float(msg.text)  # Преобразуем введенный текст в число
        if amount > balance:
            await msg.answer(text="Невозможное количество для вывода, попробуйте еще раз",
                             reply_markup=back_to_main_menu_mk)
        else:
            await state.update_data(amount=amount)  # Сохраняем сумму в состояние
            await msg.answer(text="Введите адрес для вывода:")
            await state.set_state(WithdrawInfo.ask_adress)
            print("перешли в ввод адреса")
    except ValueError:
        await msg.answer(text="Пожалуйста, введите корректное число.",
                         reply_markup=back_to_main_menu_mk)

        
@router.message(WithdrawInfo.ask_adress)
async def ask_witdraw_adress(msg: Message, state: FSMContext) -> None:
    print("спрашиваем адрес")
    data = await state.get_data()
    await state.update_data(adress = msg.text)
    await msg.answer(text=f"Подтвердите, что вы хотите вывести {data['amount']} на адрес {msg.text}",
               reply_markup=submit_mk)
 
    
@router.callback_query(F.data == 'reject')
async def rep_ask_withdraw_adres(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(text="Введите адрес еще раз",
                                  reply_markup=back_to_main_menu_mk)
    await state.set_state(WithdrawInfo.ask_adress)

    
@router.callback_query(F.data == 'submit')
async def send_transaction(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await callback.answer()
    await callback.message.answer(text="Отправка транзакции...")
    
    data = await state.get_data()
    amount = data['amount']
    adress = data['adress']
    await state.clear()
    
    connect = TonWalletSession(TC, IS_TESTNET, MAIN_ADRESS)
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    bot = callback.bot
    
    await connect.withdraw(bot, chat_id, user_id, session, amount, adress)