import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext

from database import search_products
from handlers.states import SearchStates

from keyboards import MENU_BUTTONS, get_cancel_keyboard, get_main_keyboard

from locales.ru import TEXTS as RU
from locales.en import TEXTS as EN


router = Router()


def get_texts(language: str):
    return EN if language == "en" else RU


async def perform_search(message: Message, query: str, language: str):
    texts = get_texts(language)

    try:
        products = await search_products(query)

        if not products:
            await message.answer(texts["no_products"])
            return

        lines = [
            f"{name} — {quantity}"
            for _, name, quantity in products
        ]

        await message.answer(
            f"{texts['search_results']}\n\n" + "\n".join(lines),
            reply_markup=get_main_keyboard(language),
        )

    except Exception:
        logging.exception("Search failed")

        await message.answer(
            texts["error"],
            reply_markup=get_main_keyboard(language),
        )


@router.message(F.text.in_([RU["find"], EN["find"]]))
async def start_search(message: Message, state: FSMContext):
    await state.clear()

    language = "en" if message.text == EN["find"] else "ru"
    texts = get_texts(language)

    await state.update_data(language=language)
    await state.set_state(SearchStates.waiting_for_query)

    await message.answer(
        texts["search_prompt"],
        reply_markup=get_cancel_keyboard(language),
    )


@router.message(Command("find"))
async def find_command(
    message: Message,
    command: CommandObject,
    state: FSMContext,
):
    await state.clear()

    from database import get_user_language

    language = await get_user_language(message.from_user.id) or "ru"
    texts = get_texts(language)

    query = (command.args or "").strip()

    if not query:
        await state.update_data(language=language)
        await state.set_state(SearchStates.waiting_for_query)

        await message.answer(
            texts["search_prompt"],
            reply_markup=get_cancel_keyboard(language),
        )
        return

    await perform_search(message, query, language)


@router.message(
    SearchStates.waiting_for_query,
    F.text,
    ~F.text.in_(MENU_BUTTONS),
)
async def receive_search_query(message: Message, state: FSMContext):
    language = (await state.get_data()).get("language", "ru")
    query = message.text.strip()

    if not query:
        await message.answer(get_texts(language)["search_prompt"])
        return

    await state.clear()
    await perform_search(message, query, language)


@router.message(SearchStates.waiting_for_query, ~F.text)
async def invalid_search_input(message: Message, state: FSMContext):
    language = (await state.get_data()).get("language", "ru")
    await message.answer(get_texts(language)["send_text"])