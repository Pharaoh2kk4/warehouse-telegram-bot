import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database import get_all_products
from keyboards import MENU_BUTTONS, get_main_keyboard

from locales.ru import TEXTS as RU
from locales.en import TEXTS as EN


router = Router()


async def send_stock(message: Message, language: str):
    texts = EN if language == "en" else RU

    try:
        products = await get_all_products()

        if not products:
            await message.answer(
                texts["empty_stock"],
                reply_markup=get_main_keyboard(language),
            )
            return

        lines = []
        total_units = 0

        for index, (_, name, quantity) in enumerate(products, start=1):
            lines.append(f"{index}. {name} — {quantity}")
            total_units += quantity

        footer = (
            f"\n{texts['total']}: "
            f"{len(products)} {texts['positions']}, "
            f"{total_units} {texts['units']}"
        )

        chunks = []
        current_chunk = texts["stock_title"] + "\n\n"

        for line in lines:
            if len(current_chunk) + len(line) + len(footer) > 3900:
                chunks.append(current_chunk)
                current_chunk = ""

            current_chunk += line + "\n"

        current_chunk += footer
        chunks.append(current_chunk)

        for index, chunk in enumerate(chunks):
            await message.answer(
                chunk,
                reply_markup=(
                    get_main_keyboard(language)
                    if index == len(chunks) - 1
                    else None
                ),
            )

    except Exception:
        logging.exception("Failed to get stock")

        await message.answer(
            texts["error"],
            reply_markup=get_main_keyboard(language),
        )


@router.message(F.text.in_([RU["stock"], EN["stock"]]))
async def show_stock(message: Message, state: FSMContext):
    await state.clear()

    language = "en" if message.text == EN["stock"] else "ru"
    await send_stock(message, language)


@router.message(Command("list"))
async def list_command(message: Message, state: FSMContext):
    await state.clear()

    language = await get_language(message.from_user.id)
    await send_stock(message, language)


async def get_language(user_id: int):
    from database import get_user_language

    return await get_user_language(user_id) or "ru"