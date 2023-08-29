import logging
import asyncio
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware

logging.basicConfig(level=logging.INFO)

API_TOKEN = '6535302137:AAF40uOCr-Ze8cUxZ17aMcFgwl9W08ooSQQ'
GROUP_ID = -1001879804669

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

questions = [
    'Что делал? (Укажи с разбивкой по часам) 😊',
    'Чем займешься? 🤔',
    'Круто! Есть какие-то препятствия? Что мешает? 😅',
    'Нужна помощь с задачами и планированием? 🙏',
]

responses = {}

def connect():
    return sqlite3.connect('users.db')

def create_table():
    with connect() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
        conn.commit()

def activate_user(user_id):
    with connect() as conn:
        conn.execute("INSERT OR IGNORE INTO users VALUES (?)", (user_id,))
        conn.commit()

def get_users():
    with connect() as conn:
        cursor = conn.execute("SELECT user_id FROM users")
        return [row[0] for row in cursor.fetchall()]

async def send_questions():
    while True:
        now = datetime.now()
        if (now.hour == 12 and now.minute == 0 and not now.dst()) or (now.hour == 13 and now.minute == 0 and now.dst()):
            users = get_users()
            for user_id in users:
                await bot.send_message(user_id, questions[0])
                responses[user_id] = []
            await asyncio.sleep(60)
        else:
            await asyncio.sleep(1)

@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    user_id = message.from_user.id
    activate_user(user_id)
    await message.reply("Бот активирован!")

@dp.message_handler()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    if user_id not in responses:
        responses[user_id] = []
    responses[user_id].append(message.text)
    user_responses = responses[user_id]
    if len(user_responses) < len(questions):
        next_question = questions[len(user_responses)]
        await message.reply(next_question)
    else:
        all_responses = f"{user_name}:\n"
        for i in range(len(questions)):
            all_responses += f"{questions[i]}\n{responses[user_id][i]}\n"
        await bot.send_message(GROUP_ID, all_responses, parse_mode=ParseMode.HTML)
        del responses[user_id]

if __name__ == '__main__':
    create_table()
    from aiogram import executor
    loop = asyncio.get_event_loop()
    loop.create_task(send_questions())
    executor.start_polling(dp, skip_updates=True)
