from aiogram import Bot, types
import asyncio
import logging
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.dispatcher.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aiohttp
import config
import re

logging.basicConfig(
    # указываем название с логами
    filename='log.txt',
    # указываем уровень логирования
    level=logging.INFO,
    # указываем формат сохранения логов
    format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s '
           u'[%(asctime)s] %(message)s')
storage = MemoryStorage()  # FSM
bot = Bot(token=config.botkey)
dp = Dispatcher()


@dp.message_handler(Command('start'), state=None)
async def welcome(message):
    await bot.send_message(message.chat.id, f'Здравствуйте, *{message.from_user.first_name},* бот работает\n'
                                            f'введите данные', parse_mode='Markdown')


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
