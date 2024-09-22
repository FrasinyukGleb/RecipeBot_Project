import asyncio
import aiohttp
from random import choices
from googletrans import Translator

from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()
translator = Translator()


class BotExceptions(Exception):
    pass


class Recipes(StatesGroup):
    number_of_recipes = State()
    random_recipes = State()


async def get_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            data = await resp.json()
            return data


# Обрабатываем основную команду
@router.message(Command("category_search_random"))
async def category_search_random(message: Message, command: CommandObject, state: FSMContext):
    if command.args is None:
        await message.answer("Ошибка: не указано количество интересующих рецептов. Повторите попытку.")
        return
    try:
        recipes_num = int(command.args)
    except ValueError:
        await message.answer("Ошибка: неверное значение. Укажите количество интересующих рецйептов числом.")
        return

    await state.set_data({'recipes_num': recipes_num})  # Записываем число рецептов
    data = await get_data('https://www.themealdb.com/api/json/v1/1/list.php?c=list')

    # Кнопки
    builder = ReplyKeyboardBuilder()
    for meals in data['meals']:
        builder.add(types.KeyboardButton(text=list(meals.values())[0]))
    builder.adjust(3)

    await message.answer(
        f"Выберите категорию:",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )

    await state.set_state(Recipes.number_of_recipes.state)


# Собираем список рецептов по выбранной категории
@router.message(Recipes.number_of_recipes)
async def recipes_by_category(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        num = data['recipes_num']
        recipes_in_category = await get_data(f'https://www.themealdb.com/api/json/v1/1/filter.php?c={message.text}')

        meals = recipes_in_category['meals']

        # Data
        result = choices(meals, k=num)
        ids = [i['idMeal'] for i in result]
        await state.set_data({'id': ids})

        # Перевод на русский  язык
        text = '\n'.join(i['strMeal'] for i in result)
        translation = translator.translate(text, dest='ru')

        kb = [[types.KeyboardButton(text="Покажи рецепты"), ], ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(f'Как Вам такие варианты:\n{translation.text}', reply_markup=keyboard)
        await state.set_state(Recipes.random_recipes.state)
    except BotExceptions:
        await message.answer(f"Ошибка: Попробуйте еще раз.")


# Выводим полученные рецепты отдельными сообщениями
@router.message(Recipes.random_recipes)
async def get_recipes(message: types.Message, state: FSMContext):
    try:
        random_recipes_ids = await state.get_data()
        tasks = [
            get_data(f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}') for id in random_recipes_ids['id']
        ]
        result = await asyncio.gather(*tasks)

        for meal in result:
            meal = meal['meals'][0]

            name = meal['strMeal']
            recipes = meal['strInstructions']
            img = meal['strMealThumb']
            video = meal['strYoutube']

            # Форматирование ингридиентов
            list_ingredient = []
            for i in range(1, 21):
                if (meal[f'strIngredient{i}'] != 'None'
                        and meal[f'strIngredient{i}'] is not None
                        and meal[f'strIngredient{i}'].strip() != ''):
                    list_ingredient.append(f'{meal[f"strIngredient{i}"]} - {meal[f"strMeasure{i}"]}')
            ingredients = '\n'.join(i for i in list_ingredient)

            # Перевод на русский  язык
            text = f"{name}\nFoto:\n{img}\n\nRecipe:\n{recipes}\n\nIngredients:\n{ingredients}\n\nVideo:\n{video}\n"
            translation = translator.translate(text, dest='ru')
            await message.answer(translation.text)
    except BotExceptions:
        await message.answer(f"Ошибка: Попробуйте еще раз.")
