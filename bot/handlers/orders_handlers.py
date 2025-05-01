# bot/handlers/orders_handler.py
from __future__ import annotations
from aiogram.types import FSInputFile
import random
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from datetime import datetime

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

from database.models import Datasets, Tasks, Annotations, DatasetContributions, Users, Transactions  # ORM-классы
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
        annotations_per_task=ds.annotations_per_task,
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

        # 1. Аннотация (idempotent)
        await session.execute(
            insert(Annotations)
            .values(
                task_id=task_id,
                user_id=callback.from_user.id,
                label=label_val,
            )
            .on_conflict_do_nothing()
        )

        # 2. Инкремент счётчика задач
        await session.execute(
            text("UPDATE tasks SET annotated_cnt = annotated_cnt + 1 WHERE task_id=:tid"),
            {"tid": task_id},
        )

        # 3. Учёт вклада
        await session.execute(
            insert(DatasetContributions)
            .values(
                dataset_id=dataset_id,
                user_id=callback.from_user.id,
                vote_cnt=1,
            )
            .on_conflict_do_update(
                index_elements=["dataset_id", "user_id"],
                set_={"vote_cnt": DatasetContributions.vote_cnt + 1},
            )
        )

        # 4. Закрываем задачу, если лимит набран
        await session.execute(
            text(
                """
                UPDATE tasks
                   SET status='done'
                 WHERE task_id=:tid
                   AND annotated_cnt >= (
                         SELECT annotations_per_task
                           FROM datasets
                          WHERE dataset_id=:ds
                       )
                """
            ),
            {"tid": task_id, "ds": dataset_id},
        )
        
        await session.execute(
        text("""
        /* 1. собираем количество голосов за TRUE и FALSE */
        WITH votes AS (
            SELECT
                SUM(CASE WHEN label THEN 1 ELSE 0 END) AS pos_cnt,
                SUM(CASE WHEN NOT label THEN 1 ELSE 0 END) AS neg_cnt
            FROM annotations
            WHERE task_id = :tid
        )
        /* 2. вставляем результат, только если задача уже набрала apt голосов */
        INSERT INTO task_results(task_id, final_label, confidence, closed_at)
        SELECT
            :tid                                 AS task_id,
            (pos_cnt >= neg_cnt)                 AS final_label,      /* TRUE, если победил pos */
            GREATEST(pos_cnt, neg_cnt)::numeric / :apt AS confidence, /* 0.67 при 2/1 */
            now()                                AS closed_at
        FROM votes
        WHERE (pos_cnt + neg_cnt) = :apt         /* все голоса собраны */
        ON CONFLICT (task_id) DO NOTHING
        """),
        {"tid": task_id, "apt": data["annotations_per_task"]},
        )


        # 5.  Попытка закрыть весь датасет
        await maybe_finish_dataset(session, dataset_id, callback.bot)

    # 6. Шлём следующую задачу (вне транзакции)
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
    

async def maybe_finish_dataset(session: AsyncSession, dataset_id: str, bot) -> None:
    """
    Если все tasks размечены → проставляем status='done', распределяем reward_pool.
    Запускать ТОЛЬКО внутри already-opened transaction!
    """
    # есть ли ещё живые задачи?
    remain = await session.scalar(
        select(func.count())
        .select_from(Tasks)
        .where(
            Tasks.dataset_id == dataset_id,
            Tasks.annotated_cnt < (
                select(Datasets.annotations_per_task)
                .where(Datasets.dataset_id == dataset_id)
                .scalar_subquery()
            ),
        )
    )
    if remain:        # ещё не всё размечено
        return

    # --- закрываем датасет ------------------------------------------
    ds: Datasets = await session.scalar(
        select(Datasets).where(Datasets.dataset_id == dataset_id).with_for_update()
    )
    if ds.status == "done":      # кто-то уже выплатил
        return

    ds.status = "done"
    ds.closed_at = datetime.utcnow()

    # --- распределяем деньги ---------------------------------------
    if ds.reward_pool and ds.reward_pool > 0:
        # суммарное кол-во голосов
        total_votes = await session.scalar(
            select(func.sum(DatasetContributions.vote_cnt))
            .where(DatasetContributions.dataset_id == dataset_id)
        )
        if not total_votes:
            total_votes = 0

        if total_votes == 0:
            # голосов нет — вернём деньги заказчику?
            ds.reward_pool = 0
            return

        reward_per_vote = ds.reward_pool / Decimal(total_votes)

        # берём всех участников
        rows = await session.execute(
            select(
                DatasetContributions.user_id,
                DatasetContributions.vote_cnt,
            ).where(DatasetContributions.dataset_id == dataset_id)
        )
        for uid, votes in rows:
            amount = reward_per_vote * votes

            # 1. users.balance
            await session.execute(
                text(
                    "UPDATE users SET balance = balance + :amt WHERE user_id=:uid"
                ),
                {"amt": amount, "uid": uid},
            )

        # 3. обнуляем пул
        ds.reward_pool = 0
        
        # ---------- готовим размеченный csv --------------------------
    # 1. path оригинала
        # ---------- ищем исходный файл датасета -------------------------
        result = await session.execute(
        text("""
        SELECT uri, original_name
          FROM dataset_files
         WHERE dataset_id = :ds
         ORDER BY file_id
         LIMIT 1
        """),
        {"ds": dataset_id},
        )
        file_rec = result.first()        # 👈 берём первую строку

        if not file_rec:                 # могло не быть файла
            return

        uri, orig_name = file_rec        # теперь безопасно
        orig_path = f"Datasets/{uri.split('tg://')[-1]}"   # твоя логика путей

        import pandas as pd, os, json, tempfile

        df = pd.read_csv(orig_path, header=None, names=["text"])
        res = await session.execute(
            text(
            "SELECT task_id, final_label FROM task_results "
            "JOIN tasks USING(task_id) "
            "WHERE dataset_id=:ds ORDER BY task_id"
            ),
            {"ds": dataset_id},
        )
        labels = [row.final_label for row in res]
        df["label"] = labels

        tmpdir = tempfile.gettempdir()
        out_path = os.path.join(tmpdir, f"{dataset_id}_labeled.csv")
        df.to_csv(out_path, index=False)

    # ---------- шлём автору --------------------------------------
        nice_name = f"{ds.name}_labeled.csv"
        
    
        await bot.send_document(
            chat_id=ds.user_id,
            document=FSInputFile(out_path, filename=nice_name),
            caption=(
                f"✅ Ваш датасет <b>{ds.name}</b> размечен!\n"
                f"Прикреплён файл из <b>{len(df)}</b> строк с финальными метками."
            ),
            parse_mode="HTML",
        )

