import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_all_products, get_product_by_id, delete_product
from handlers.states import DeleteStates

from keyboards import (
    get_products_keyboard,
    get_confirmation_keyboard,
    get_main_keyboard,
)

from locales.ru import TEXTS as RU
from locales.en import TEXTS as EN


router = Router()


def get_texts(language: str):
    return EN if language == "en" else RU


@router.message(F.text.in_([RU["delete"], EN["delete"]]))
async def start_delete(message: Message, state: FSMContext):
    await state.clear()

    language = "en" if message.text == EN["delete"] else "ru"
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
        texts["select_delete"],
        reply_markup=get_products_keyboard(products, "delete"),
    )


@router.callback_query(F.data.startswith("delete:"))
async def delete_callback(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")

    language = (await state.get_data()).get("language", "ru")
    texts = get_texts(language)

    if action[1] == "cancel":
        await state.clear()

        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            texts["cancelled"],
            reply_markup=get_main_keyboard(language),
        )

        await callback.answer()
        return

    if action[1] == "confirm":
        data = await state.get_data()

        user = callback.from_user
        user_name = user.full_name or user.username or str(user.id)

        try:
            result = await delete_product(
                product_id=data["product_id"],
                user_id=user.id,
                user_name=user_name,
            )

            await state.clear()
            await callback.message.edit_reply_markup(reply_markup=None)

            if result is None:
                await callback.message.answer(
                    texts["not_found"],
                    reply_markup=get_main_keyboard(language),
                )
            else:
                name, quantity = result

                await callback.message.answer(
                    f"{texts['deleted']}\n"
                    f"{name} — {quantity}",
                    reply_markup=get_main_keyboard(language),
                )

        except Exception:
            logging.exception("Failed to delete product")
            await state.clear()

            await callback.message.answer(
                texts["error"],
                reply_markup=get_main_keyboard(language),
            )

        await callback.answer()
        return

    try:
        product_id = int(action[1])
    except (ValueError, IndexError):
        await callback.answer("Invalid product", show_alert=True)
        return

    product = await get_product_by_id(product_id)

    if not product:
        await callback.answer(texts["not_found"], show_alert=True)
        return

    _, name, quantity = product

    await state.update_data(
        product_id=product_id,
        product_name=name,
    )

    await state.set_state(DeleteStates.waiting_for_confirmation)

    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(
        f"{texts['confirm_delete']}\n\n"
        f"{name} — {quantity}",
        reply_markup=get_confirmation_keyboard(language),
    )

    await callback.answer()