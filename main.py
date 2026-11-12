import asyncio
import logging

from typing import Any, Awaitable, Callable

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject

from config import BOT_TOKEN, ALLOWED_USERS
from database import init_db

from handlers.common import router as common_router
from handlers.add_product import router as add_product_router
from handlers.stock import router as stock_router
from handlers.write_off import router as write_off_router
from handlers.search import router as search_router
from handlers.delete import router as delete_router
from handlers.history import router as history_router


class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, dict[str, Any]],
            Awaitable[Any]
        ],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")

        if user is None or user.id not in ALLOWED_USERS:
            if hasattr(event, "answer"):
                await event.answer("Access denied.")
            return None

        return await handler(event, data)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    dp = Dispatcher()

    dp.message.middleware(AccessMiddleware())
    dp.callback_query.middleware(AccessMiddleware())

    dp.include_router(common_router)
    dp.include_router(add_product_router)
    dp.include_router(stock_router)
    dp.include_router(write_off_router)
    dp.include_router(search_router)
    dp.include_router(delete_router)
    dp.include_router(history_router)

    logging.info("Warehouse bot is running")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())