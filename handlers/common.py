from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database import get_user_language, set_user_language

from keyboards import (
    get_language_keyboard,
    get_main_keyboard,
)

from locales.ru import TEXTS as RU
from locales.en import TEXTS as EN


router = Router()


async def get_texts(user_id: int):
    language = await get_user_language(user_id)

    return (
        language or "ru",
        RU if language != "en" else EN,
    )


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()

    language = await get_user_language(message.from_user.id)

    if language is None:
        await message.answer(
            RU["choose_language"],
            reply_markup=get_language_keyboard(),
        )
        return

    texts = RU if language == "ru" else EN

    await message.answer(
        texts["welcome"],
        reply_markup=get_main_keyboard(language),
    )


@router.callback_query(F.data.startswith("language:"))
async def language_callback(callback, state: FSMContext):
    language = callback.data.split(":")[1]

    if language not in ("ru", "en"):
        await callback.answer("Invalid language")
        return

    await set_user_language(callback.from_user.id, language)
    await state.clear()

    texts = RU if language == "ru" else EN

    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(
        texts["language_saved"],
        reply_markup=get_main_keyboard(language),
    )

    await callback.answer()


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    language, texts = await get_texts(message.from_user.id)

    await state.clear()

    await message.answer(
        texts["cancelled"],
        reply_markup=get_main_keyboard(language),
    )


@router.message(F.text.in_([RU["cancel"], EN["cancel"]]))
async def cancel_button_handler(message: Message, state: FSMContext):
    language = "en" if message.text == EN["cancel"] else "ru"
    texts = EN if language == "en" else RU

    await state.clear()

    await message.answer(
        texts["cancelled"],
        reply_markup=get_main_keyboard(language),
    )


@router.message(F.text.in_([RU["language"], EN["language"]]))
async def change_language_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        RU["choose_language"],
        reply_markup=get_language_keyboard(),
    )