import asyncio

from deskconn.database import database


async def main():
    await database.init_db()


asyncio.run(main())
