import asyncio
import time
import qrcode
from tonutils.client import TonapiClient
from tonutils.wallet import WalletV4R2, WalletV5R1
from aiogram import Bot
from config import MAIN_MNEMONIC
from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_user import orm_update_balance


class TonWalletSession:
    def __init__(self, api_key: str, is_testnet: bool, destination_address: str):
        self.client = TonapiClient(api_key=api_key, is_testnet=is_testnet)
        self.wallet, self.public_key, self.private_key, self.mnemonic = WalletV4R2.create(self.client)
        self.destination_address = destination_address
        self.amount = 0

        
    async def withdraw(self, bot: Bot, chat_id: int, user_id: int, session: AsyncSession, amount, adress: str):
        wallet = WalletV5R1.from_mnemonic(self.client, MAIN_MNEMONIC)
        try:
            tx_hash = await wallet[0].transfer(
                    destination=adress,
                    amount=amount-0.02,
                )
            await orm_update_balance(session, tx_hash, user_id, amount, 'withdraw', adress)
            await bot.send_message(chat_id, f"Вывод средств выполнен, хэш транзакции: {tx_hash}")
        except Exception as e:
            withdraw_error_message = f"Непредвиденная ошибка {e} вывода, повторите попытку позже"
            print(withdraw_error_message)
            await bot.send_message(chat_id, withdraw_error_message)
         

    async def wait_for_deposit(self, bot: Bot, chat_id: int, user_id: int, session: AsyncSession, attempts: int = 4, delay: int = 15):
        ok = False
        for i in range(attempts):
            try:
                balance = await self.wallet.balance()
                ok = True
                message = f"Проверка {i}, баланс: {(balance) / 1e9} TON"
                print(message)

                if balance > self.amount:
                    deposit_amount = (balance - self.amount) / 1e9
                    self.amount = balance
                    deposit_message = f"Принято пополнение {deposit_amount} TON, ожидайте зачисление на баланс в течение 15 минут"
                    print(deposit_message)
                    await bot.send_message(chat_id, deposit_message)
            except:
                error_message = f"Проверка {i}, Кошелька нет еще"
                print(error_message)

            await asyncio.sleep(delay)
        
        if ok:
            await self.deploy_wallet()
            time.sleep(10)
            await self.transfer_funds(session, user_id)
        
        return ok

    async def deploy_wallet(self):
        tx_hash = await self.wallet.deploy()
        print(f"Wallet deployed successfully!")
        print(f"Wallet address: {self.wallet.address.to_str()}")
        print(f"Transaction hash: {tx_hash}")

    async def transfer_funds(self, session: AsyncSession, user_id):
        try:
            print("Начало отправки")
            tx_hash = await self.wallet.transfer(
                destination=self.destination_address,
                amount=self.amount / 1e9 - 0.01,
            )
            print(f"Successfully transferred TON!")
            print(f"Transaction hash: {tx_hash}")
            await orm_update_balance(session, tx_hash, user_id, self.amount/1e9, 'deposit')
            
        except Exception as e:
            print(f"Не удалось вывести, Ошибка: {e}")

    async def run(self):
        self.display_wallet_info()
        self.request_deposit()
        time.sleep(2)
        
        if await self.wait_for_deposit():
            await self.deploy_wallet()
            time.sleep(10)
            await self.transfer_funds()   