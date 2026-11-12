from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from locales.ru import TEXTS as RU
from locales.en import TEXTS as EN


MENU_BUTTONS = (
    RU["add_product"],
    EN["add_product"],
    RU["write_off"],
    EN["write_off"],
    RU["stock"],
    EN["stock"],
    RU["find"],
    EN["find"],
    RU["delete"],
    EN["delete"],
    RU["history"],
    EN["history"],
    RU["language"],
    EN["language"],
    RU["cancel"],
    EN["cancel"],
)


def get_language_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇷🇺 Русский",
                    callback_data="language:ru",
                ),
                InlineKeyboardButton(
                    text="🇬🇧 English",
                    callback_data="language:en",
                ),
            ]
        ]
    )


def get_main_keyboard(language: str):
    texts = RU if language == "ru" else EN

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=texts["add_product"]),
                KeyboardButton(text=texts["write_off"]),
            ],
            [
                KeyboardButton(text=texts["stock"]),
                KeyboardButton(text=texts["find"]),
            ],
            [
                KeyboardButton(text=texts["delete"]),
                KeyboardButton(text=texts["history"]),
            ],
            [
                KeyboardButton(text=texts["language"]),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=texts["main_menu"],
    )


def get_cancel_keyboard(language: str):
    texts = RU if language == "ru" else EN

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts["cancel"])]
        ],
        resize_keyboard=True,
    )


def get_products_keyboard(products, action: str):
    buttons = []

    for product_id, name, quantity in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"{name} — {quantity}",
                callback_data=f"{action}:{product_id}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirmation_keyboard(language: str):
    texts = RU if language == "ru" else EN

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts["confirm"],
                    callback_data="delete:confirm",
                ),
                InlineKeyboardButton(
                    text=texts["cancel"],
                    callback_data="delete:cancel",
                ),
            ]
        ]
    )