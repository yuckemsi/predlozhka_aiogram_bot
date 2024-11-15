import asyncio
import logging
from config import TOKEN
from aiogram import Bot, Dispatcher

from app.database.db import db_connect
from app.handlers import rt

bot = Bot(token=TOKEN)

async def main():
    await db_connect()
    dp = Dispatcher()
    dp.include_router(rt)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот отключен')
