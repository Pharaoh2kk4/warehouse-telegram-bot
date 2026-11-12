import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import get_operation_history
from keyboards import get_main_keyboard

from locales.ru import TEXTS as RU
from locales.en import TEXTS as EN


router = Router()


@router.message(F.text.in_([RU["history"], EN["history"]]))
async def show_history(message: Message, state: FSMContext):
    await state.clear()

    language = "en" if message.text == EN["history"] else "ru"
    texts = EN if language == "en" else RU

    try:
        operations = await get_operation_history(20)

        if not operations:
            await message.answer(
                texts["history_empty"],
                reply_markup=get_main_keyboard(language),
            )
            return

        action_names = {
            "add": texts["action_add"],
            "remove": texts["action_remove"],
            "delete": texts["action_delete"],
        }

        lines = []

        for name, user_name, delta, action, created_at in operations:
            action_text = action_names.get(action, action)

            lines.append(
                f"📦 {name}\n"
                f"👤 {user_name}\n"
                f"⚙️ {action_text}: {delta:+d}\n"
                f"🕒 {created_at}"
            )

        await message.answer(
            f"{texts['history_title']}\n\n" + "\n\n".join(lines),
            reply_markup=get_main_keyboard(language),
        )

    except Exception:
        logging.exception("Failed to get operation history")

        await message.answer(
            texts["error"],
            reply_markup=get_main_keyboard(language),
        )