# bot/handlers/orders_handler.py
from __future__ import annotations

import random
from datetime import datetime
from decimal import Decimal

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, text, func, update
from sqlalchemy.dialects.postgresql import insert 
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Datasets, Tasks, Annotations  # ORM-классы
from bot.keyboards.user_keyboards import back_to_main_menu

router = Router()


# ===============================================================
#   FSM
# ===============================================================
class Labeling(StatesGroup):
    dataset_id = State()      # str
    pos_label  = State()      # str
    neg_label  = State()      # str
    in_progress = State()     # пользователь сейчас размечает


# ===============================================================
#   Вспомогательные клавиатуры
# ===============================================================
def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardBuilder().add(back_to_main_menu).as_markup()


# ===============================================================
#   Главное меню «Заказы»
# ===============================================================
@router.callback_query(F.data == "orders_menu")
async def orders_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    kb, count = await build_orders_keyboard(session)
    if count:
        await callback.message.edit_text(
            "Выберите датасет для разметки 👇",
            reply_markup=kb,
        )
    else:
        await callback.message.edit_text(
            "Пока нет открытых заказов. Загляните позже!",
            reply_markup=back_kb(),
        )


async def build_orders_keyboard(
    session: AsyncSession,
) -> tuple[InlineKeyboardMarkup, int]:
    """Собираем список датасетов со статусом 'labeling'."""
    stmt = (
        select(
            Datasets.dataset_id,
            Datasets.name,
        )
        .where(Datasets.status == "labeling")
        .order_by(Datasets.name)
    )
    rows = (await session.execute(stmt)).all()

    kb = InlineKeyboardBuilder()
    for ds_id, name in rows:
        kb.add(
            InlineKeyboardButton(
                text=name,
                callback_data=f"order_info_{ds_id}",
            )
        )
    kb.add(back_to_main_menu)
    return kb.adjust(1).as_markup(), len(rows)


# ===============================================================
#   Карточка датасета + кнопка «Разметить»
# ===============================================================
@router.callback_query(lambda c: c.data.startswith("order_info_"))
async def order_info(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await callback.answer()
    dataset_id = callback.data.split("_", 2)[2]

    ds: Datasets | None = (
        await session.scalar(
            select(Datasets).where(Datasets.dataset_id == dataset_id)
        )
    )
    if not ds:
        return await callback.message.edit_text(
            "Датасет не найден 🤷‍♂️", reply_markup=back_kb()
        )

    pos = ds.labels.get("pos", "positive")
    neg = ds.labels.get("neg", "negative")

    # Сколько заданий ещё не закрыто
    remain = await session.scalar(
        select(func.count())
        .select_from(Tasks)
        .where(
            Tasks.dataset_id == dataset_id,
            Tasks.annotated_cnt < ds.annotations_per_task,
        )
    )

    info = (
        f"📦 <b>{ds.name}</b>\n"
        f"{ds.description or '_без описания_'}\n\n"
        f"Всего заданий: {remain}\n"
        f"Классы: <code>{pos}</code> / <code>{neg}</code>\n"
        f"Пул наград: {ds.reward_pool} TON\n"
    )

    kb = (
        InlineKeyboardBuilder()
        .button(
            text="🚀 Разметить",
            callback_data=f"label_start_{dataset_id}",
        )
        .add(back_to_main_menu)
        .as_markup()
    )

    await callback.message.edit_text(
        info, reply_markup=kb, parse_mode="HTML"
    )


# ===============================================================
#   Старт разметки
# ===============================================================
@router.callback_query(lambda c: c.data.startswith("label_start_"))
async def start_labeling(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await callback.answer()
    dataset_id = callback.data.split("_", 2)[2]

    ds: Datasets | None = (
        await session.scalar(
            select(Datasets).where(Datasets.dataset_id == dataset_id)
        )
    )
    if not ds:
        return await callback.message.answer("Что-то пошло не так…")

    await state.set_state(Labeling.in_progress)
    await state.update_data(
        dataset_id=dataset_id,
        pos=ds.labels["pos"],
        neg=ds.labels["neg"],
    )

    await send_next_task(
        chat_id=callback.from_user.id,
        session=session,
        state=state,
        bot=callback.bot,
    )


# ===============================================================
#   Кнопки ответов на задачу
# ===============================================================
@router.callback_query(lambda c: c.data.startswith("answer_"), Labeling.in_progress)
async def handle_answer(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await callback.answer()
    _, task_id_str, label_str = callback.data.split("_", 2)
    task_id = int(task_id_str)
    label_val = label_str == "pos"

    data = await state.get_data()
    dataset_id: str = data["dataset_id"]

    async with session.begin():
        # 1. Записываем аннотацию (если её ещё нет)
        await session.execute(
    insert(Annotations)          # ← теперь это Postgres-insert
        .values(
            task_id=task_id,
            user_id=callback.from_user.id,
            label=label_val,
        )
        .on_conflict_do_nothing()
)

        # 2. Обновляем счётчик
        await session.execute(
            text(
                """
                update tasks
                set annotated_cnt = annotated_cnt + 1
                where task_id = :tid
                """
            ),
            {"tid": task_id},
        )

        # 3. Если задача набрала нужное число голосов — закрываем
        await session.execute(
            text(
                """
                update tasks
                set status='done'
                where task_id = :tid
                  and annotated_cnt >= (
                        select annotations_per_task
                        from datasets
                        where dataset_id = :ds
                  )
                """
            ),
            {"tid": task_id, "ds": dataset_id},
        )

    # 4. Отправляем следующую
    await send_next_task(
        chat_id=callback.from_user.id,
        session=session,
        state=state,
        bot=callback.bot,
    )


# ===============================================================
#   Выдать пользователю следующую строку
# ===============================================================
async def send_next_task(
    *,
    chat_id: int,
    session: AsyncSession,
    state: FSMContext,
    bot,
) -> None:
    data = await state.get_data()
    dataset_id: str = data["dataset_id"]
    pos = data["pos"]
    neg = data["neg"]

    # ----------------------------------------------------------
    #   Берём одну незакрытую задачу, которую юзер ещё не делал
    # ----------------------------------------------------------
    row = await session.execute(
        text(
            """
            with candidate as (
                select task_id, text_row
                from tasks
                where dataset_id = :ds
                  and annotated_cnt < (
                        select annotations_per_task
                        from datasets where dataset_id = :ds
                  )
                  and not exists (
                        select 1
                        from annotations
                        where annotations.task_id = tasks.task_id
                          and annotations.user_id = :uid
                  )
                order by random()
                limit 1
                for update skip locked
            )
            select task_id, text_row from candidate
            """
        ),
        {"ds": dataset_id, "uid": chat_id},
    )
    task = row.first()

    if not task:
        # Всё размечено пользователем
        await bot.send_message(chat_id, "🎉 Вы размечали всё, что могли. Спасибо!")
        await state.clear()
        return

    task_id, text_row = task

    kb = (
        InlineKeyboardBuilder()
        .button(
            text=pos,
            callback_data=f"answer_{task_id}_pos",
        )
        .button(
            text=neg,
            callback_data=f"answer_{task_id}_neg",
        )
        .as_markup()
    )

    await bot.send_message(
        chat_id,
        f"<b>Задача #{task_id}</b>\n\n{text_row}",
        reply_markup=kb,
        parse_mode="HTML",
    )
