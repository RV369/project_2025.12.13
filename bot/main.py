import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from .nlp import text_to_sql_result

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError('BOT_TOKEN не задан в переменных окружения')

# Используем DefaultBotProperties
bot = Bot(
    token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


@dp.message(Command('start'))
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f'Привет, {hbold(message.from_user.full_name)}! '
        f'Задай мне вопрос по статистике видео.',
    )


@dp.message()
async def handle_text_query(message: Message) -> None:
    try:
        result = text_to_sql_result(message.text)
        await message.answer(str(result))
    except Exception as e:
        logger.error(f'Ошибка при обработке запроса: {e}', exc_info=True)
        await message.answer(
            'Не удалось обработать ваш запрос. Попробуйте переформулировать.',
        )


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
