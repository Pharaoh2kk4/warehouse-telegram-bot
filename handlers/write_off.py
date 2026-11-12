import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_all_products, write_off_product
from handlers.states import WriteOffStates

from keyboards import (
    MENU_BUTTONS,
    get_products_keyboard,
    get_cancel_keyboard,
    get_main_keyboard,
)

from locales.ru import TEXTS as RU
from locales.en import TEXTS as EN


router = Router()


def get_texts(language: str):
    return EN if language == "en" else RU


@router.message(F.text.in_([RU["write_off"], EN["write_off"]]))
async def start_write_off(message: Message, state: FSMContext):
    await state.clear()

    language = "en" if message.text == EN["write_off"] else "ru"
    texts = get_texts(language)

    products = await get_all_products()

    if not products:
        await message.answer(
            texts["empty_stock"],
            reply_markup=get_main_keyboard(language),
        )
        return

    await state.update_data(language=language)

    await message.answer(
        texts["select_product"],
        reply_markup=get_products_keyboard(products, "writeoff"),
    )


@router.callback_query(F.data.startswith("writeoff:"))
async def select_write_off_product(
    callback: CallbackQuery,
    state: FSMContext,
):
    product_id = int(callback.data.split(":")[1])

    language = (await state.get_data()).get("language", "ru")
    texts = get_texts(language)

    from database import get_product_by_id

    product = await get_product_by_id(product_id)

    if not product:
        await callback.answer(texts["not_found"], show_alert=True)
        return

    _, name, quantity = product

    await state.update_data(
        product_id=product_id,
        product_name=name,
        available_quantity=quantity,
    )

    await state.set_state(WriteOffStates.waiting_for_quantity)

    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(
        f"{name}\n"
        f"{texts['available']}: {quantity}\n"
        f"{texts['enter_writeoff']}",
        reply_markup=get_cancel_keyboard(language),
    )

    await callback.answer()


@router.message(
    WriteOffStates.waiting_for_quantity,
    F.text,
    ~F.text.in_(MENU_BUTTONS),
)
async def receive_write_off_quantity(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()
    language = data.get("language", "ru")
    texts = get_texts(language)

    raw_quantity = message.text.strip()

    if not raw_quantity.isdecimal():
        await message.answer(texts["invalid_quantity"])
        return

    quantity = int(raw_quantity)

    if not 1 <= quantity <= 1_000_000:
        await message.answer(texts["invalid_quantity"])
        return

    user = message.from_user
    user_name = user.full_name or user.username or str(user.id)

    try:
        result = await write_off_product(
            product_id=data["product_id"],
            quantity=quantity,
            user_id=user.id,
            user_name=user_name,
        )

        if result == "not_found":
            await message.answer(texts["not_found"])
        elif result == "insufficient":
            await message.answer(
                f"{texts['insufficient_stock']}\n"
                f"{texts['available']}: {data['available_quantity']}"
            )
            return
        else:
            await message.answer(
                f"{texts['writeoff_success']}\n"
                f"{data['product_name']}: -{quantity}\n"
                f"{texts['remaining']}: {result}",
                reply_markup=get_main_keyboard(language),
            )

        await state.clear()

    except Exception:
        logging.exception("Failed to write off product")
        await state.clear()

        await message.answer(
            texts["error"],
            reply_markup=get_main_keyboard(language),
        )


@router.message(
    WriteOffStates.waiting_for_quantity,
    ~F.text,
)
async def invalid_write_off_input(
    message: Message,
    state: FSMContext,
):
    language = (await state.get_data()).get("language", "ru")
    await message.answer(get_texts(language)["send_text"])