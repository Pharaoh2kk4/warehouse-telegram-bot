import asyncio
import aiohttp


async def main():
    url = "https://api.telegram.org"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print("Connection successful!")
                print("HTTP status:", response.status)

    except Exception as error:
        print("Connection failed:", repr(error))


if __name__ == "__main__":
    asyncio.run(main())
