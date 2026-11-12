from pathlib import Path

import aiosqlite


DB_PATH = Path(__file__).resolve().parent / "sklad.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0
                    CHECK(quantity >= 0),
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                delta INTEGER NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT NOT NULL DEFAULT 'ru'
                    CHECK(language IN ('ru', 'en'))
            )
        """)

        await db.commit()


def normalize_name(name: str) -> str:
    return " ".join(name.split()).casefold()


async def get_user_language(user_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT language FROM users WHERE user_id = ?",
            (user_id,),
        )

        row = await cursor.fetchone()
        return row[0] if row else None


async def set_user_language(user_id: int, language: str):
    if language not in ("ru", "en"):
        raise ValueError("Unsupported language")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, language)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET language = excluded.language
        """, (user_id, language))

        await db.commit()


async def add_product(
    name: str,
    quantity: int,
    user_id: int,
    user_name: str,
):
    normalized_name = normalize_name(name)
    display_name = " ".join(name.split())

    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        await db.execute("PRAGMA busy_timeout=30000")
        await db.execute("BEGIN IMMEDIATE")

        cursor = await db.execute(
            "SELECT id FROM products WHERE name = ?",
            (normalized_name,),
        )

        product = await cursor.fetchone()

        if product:
            await db.execute("""
                UPDATE products
                SET quantity = quantity + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (quantity, product[0]))
        else:
            await db.execute("""
                INSERT INTO products (name, display_name, quantity)
                VALUES (?, ?, ?)
            """, (normalized_name, display_name, quantity))

        await db.execute("""
            INSERT INTO operations (
                product_name, user_id, user_name, delta, action
            )
            VALUES (?, ?, ?, ?, 'add')
        """, (display_name, user_id, user_name, quantity))

        await db.commit()


async def get_all_products():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, display_name, quantity
            FROM products
            ORDER BY display_name COLLATE NOCASE
        """)

        return await cursor.fetchall()


async def get_product_by_id(product_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, display_name, quantity
            FROM products
            WHERE id = ?
        """, (product_id,))

        return await cursor.fetchone()


async def write_off_product(
    product_id: int,
    quantity: int,
    user_id: int,
    user_name: str,
):
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        await db.execute("PRAGMA busy_timeout=30000")
        await db.execute("BEGIN IMMEDIATE")

        cursor = await db.execute("""
            SELECT display_name, quantity
            FROM products
            WHERE id = ?
        """, (product_id,))

        product = await cursor.fetchone()

        if not product:
            await db.rollback()
            return "not_found"

        name, current_quantity = product

        if quantity > current_quantity:
            await db.rollback()
            return "insufficient"

        await db.execute("""
            UPDATE products
            SET quantity = quantity - ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (quantity, product_id))

        await db.execute("""
            INSERT INTO operations (
                product_name, user_id, user_name, delta, action
            )
            VALUES (?, ?, ?, ?, 'remove')
        """, (name, user_id, user_name, -quantity))

        await db.commit()

        return current_quantity - quantity


async def search_products(query: str):
    normalized_query = normalize_name(query)

    products = await get_all_products()

    return [
        product
        for product in products
        if normalized_query in normalize_name(product[1])
    ]


async def delete_product(
    product_id: int,
    user_id: int,
    user_name: str,
):
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        await db.execute("PRAGMA busy_timeout=30000")
        await db.execute("BEGIN IMMEDIATE")

        cursor = await db.execute("""
            SELECT display_name, quantity
            FROM products
            WHERE id = ?
        """, (product_id,))

        product = await cursor.fetchone()

        if not product:
            await db.rollback()
            return None

        name, quantity = product

        await db.execute(
            "DELETE FROM products WHERE id = ?",
            (product_id,),
        )

        await db.execute("""
            INSERT INTO operations (
                product_name, user_id, user_name, delta, action
            )
            VALUES (?, ?, ?, ?, 'delete')
        """, (name, user_id, user_name, -quantity))

        await db.commit()

        return name, quantity


async def get_operation_history(limit: int = 20):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT
                product_name,
                user_name,
                delta,
                action,
                created_at
            FROM operations
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        return await cursor.fetchall()