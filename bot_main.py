import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram import F
from aiogram.utils.formatting import Bold, as_list, as_marked_section

from token_data import TOKEN
from recipes_handler import router

dp = Dispatcher()
dp.include_router(router)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    kb = [
        [
          types.KeyboardButton(text="Команды"),
          types.KeyboardButton(text="Описание бота"),
        ],
    ]

    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer(f"Привет, {hbold(message.from_user.full_name)}! С чего начнем?", reply_markup=keyboard)


@dp.message(F.text.lower() == "команды")
async def commands(message: types.Message):
    response = as_list(as_marked_section(
        Bold("Команды:"),
        "/category_search_random <количество> - "
        "показывает указанное количество рецептов",
        marker="✅ ",
    ), )
    await message.answer(**response.as_kwargs())


@dp.message(F.text.lower() == "описание бота")
async def description(message: types.Message):
    await message.answer("Данный бот предоставляет информацию о рецептах, "
                         "ингредиентах и категориях блюд из API themealdb.")


async def main() -> None:
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())