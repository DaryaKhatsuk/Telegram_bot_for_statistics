import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types, F
# from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.command import Command
from datetime import datetime
from pymongo import MongoClient
import subprocess
import bson
import os
from config import botkey, mongo_connection


# Подключение к MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
collection = db['payments']


# storage = MemoryStorage()  # FSM
logging.basicConfig(
    # указываем название с логами
    filename='log.txt',
    # указываем уровень логирования
    level=logging.INFO,
    # указываем формат сохранения логов
    format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s '
           u'[%(asctime)s] %(message)s')
bot = Bot(token=botkey)
dp = Dispatcher()


@dp.message(Command('start'))
async def welcome(message):
    await bot.send_message(message.chat.id, f'Здравствуйте, *{message.from_user.first_name},* бот работает\n'
                                            f'введите данные', parse_mode='Markdown')


def is_collection_empty():
    return collection.count_documents({}) == 0


def restore_data_from_file():
    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, "dump", "sampleDB", "sample_collection.bson")

    with open(file_path, "rb") as f:
        # Читаем содержимое файла как BSON-документы
        data = bson.decode_all(f.read())
        # Вставляем документы в коллекцию MongoDB
        collection.insert_many(data)


# Функция для агрегации данных
async def aggregate_payments(dt_from, dt_upto, group_type):
    # Определение временных интервалов для агрегации
    dt_from = datetime.fromisoformat(dt_from)
    dt_upto = datetime.fromisoformat(dt_upto)

    print('dt_from, dt_upto', dt_from, dt_upto)
    print(group_type)
    # interval = {'hour': '%H:%M:%S', 'day': '%Y-%m-%dT%H:%M:%S', 'month': '%Y-%m'}[group_type]
    # print('interval', interval)
    date_formats = {
        "year": "%Y", "month": "%Y-%m", "day": "%Y-%m-%d", "hour": "%Y-%m-%dT%H", "minute": "%Y-%m-%dT%H:%M:%S"
    }
    # date_formats = ["%Y", "%Y-%m", "%Y-%m-%d", "%Y-%m-%dT%H", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"]
    if date_formats.get(group_type):
        print(date_formats.get(group_type))
        date_for = date_formats.get(group_type)
    else:
        date_for = "%Y-%m-%dT%H:%M:%S"
    pipeline = [
        {"$match": {"dt": {"$gte": dt_from, "$lte": dt_upto}}},
        {"$group": {
            "_id": {
            "$dateToString": {
                "format": date_for,
                "date": "$dt"
            }
        },
            "total_value": {"$sum": "$value"}
        }},
        {"$sort": {"_id": 1}}
    ]
    print(pipeline)

    aggregated_data = list(collection.aggregate(pipeline))
    print(aggregated_data)
    # Форматирование результатов агрегации
    dataset = [item['total_value'] for item in aggregated_data]

    labels = []
    for item in aggregated_data:
        for data_type, form in date_formats.items():
            try:
                dt = datetime.strptime(item['_id'], form)
                labels.append(dt.strftime('%Y-%m%dT%H:%M:%S'))
                break
            except ValueError:
                continue
    print(dataset, labels)
    return {'dataset': dataset, 'labels': labels}


@dp.message(F.text)
async def handle_message(message: types.Message):
    try:
        # Парсинг JSON из текста сообщения
        data = json.loads(message.text)
        print(data)
        # Вызов агрегации данных
        result = await aggregate_payments(data['dt_from'], data['dt_upto'], data['group_type'])
        print(result)

        # Отправка ответа пользователю
        await message.answer(json.dumps(result, indent=4), parse_mode=ParseMode.MARKDOWN)
        # await message.answer(json.dumps(result, indent=4), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await message.reply(f'Error: {e}')


# Запуск процесса поллинга новых апдейтов
async def main():
    if is_collection_empty():
        restore_data_from_file()
    await dp.start_polling(bot)

# # Запуск бота
# if __name__ == '__main__':
#     asyncio.run(dp.start_polling())
if __name__ == "__main__":
    asyncio.run(main())
