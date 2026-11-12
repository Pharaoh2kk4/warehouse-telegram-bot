import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import add_product
from handlers.states import AddProductStates

from keyboards import (
    MENU_BUTTONS,
    get_cancel_keyboard,
    get_main_keyboard,
)

from locales.ru import TEXTS as RU
from locales.en import TEXTS as EN


router = Router()


def get_texts(language: str):
    return EN if language == "en" else RU


@router.message(F.text.in_([RU["add_product"], EN["add_product"]]))
async def start_add_product(message: Message, state: FSMContext):
    await state.clear()

    language = "en" if message.text == EN["add_product"] else "ru"
    texts = get_texts(language)

    await state.update_data(language=language)
    await state.set_state(AddProductStates.waiting_for_name)

    await message.answer(
        texts["enter_product_name"],
        reply_markup=get_cancel_keyboard(language),
    )


@router.message(
    AddProductStates.waiting_for_name,
    F.text,
    ~F.text.in_(MENU_BUTTONS),
)
async def receive_product_name(message: Message, state: FSMContext):
    language = (await state.get_data()).get("language", "ru")
    texts = get_texts(language)

    name = " ".join(message.text.split())

    if not 2 <= len(name) <= 100:
        await message.answer(texts["invalid_name"])
        return

    await state.update_data(product_name=name)
    await state.set_state(AddProductStates.waiting_for_quantity)

    await message.answer(texts["enter_quantity"])


@router.message(
    AddProductStates.waiting_for_quantity,
    F.text,
    ~F.text.in_(MENU_BUTTONS),
)
async def receive_product_quantity(message: Message, state: FSMContext):
    language = (await state.get_data()).get("language", "ru")
    texts = get_texts(language)

    raw_quantity = message.text.strip()

    if not raw_quantity.isdecimal():
        await message.answer(texts["invalid_quantity"])
        return

    quantity = int(raw_quantity)

    if not 1 <= quantity <= 1_000_000:
        await message.answer(texts["invalid_quantity"])
        return

    data = await state.get_data()
    product_name = data["product_name"]

    user = message.from_user
    user_name = user.full_name or user.username or str(user.id)

    try:
        await add_product(
            name=product_name,
            quantity=quantity,
            user_id=user.id,
            user_name=user_name,
        )

        await state.clear()

        await message.answer(
            f"{texts['product_added']}\n"
            f"{product_name}: +{quantity}",
            reply_markup=get_main_keyboard(language),
        )

    except Exception:
        logging.exception("Failed to add product")
        await state.clear()

        await message.answer(
            texts["error"],
            reply_markup=get_main_keyboard(language),
        )


@router.message(
    AddProductStates.waiting_for_name,
    ~F.text,
)
@router.message(
    AddProductStates.waiting_for_quantity,
    ~F.text,
)
async def invalid_product_input(message: Message, state: FSMContext):
    language = (await state.get_data()).get("language", "ru")
    texts = get_texts(language)

    await message.answer(texts["send_text"])