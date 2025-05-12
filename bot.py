import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv
from database import init_db, get_or_create_user, update_user_preferences
from model import BookRecommender

# Инициализация
load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
recommender = BookRecommender()

# Состояния
class BookRating(StatesGroup):
    waiting_for_book_title = State()
    waiting_for_rating = State()

# Команды
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user = get_or_create_user(message.from_user.id)
    await message.answer(
        "📚 Добро пожаловать в BookRecommendBot!\n\n"
        "Я могу порекомендовать вам книги на основе ваших предпочтений.\n"
        "Используйте команды:\n"
        "/rate - оценить книгу\n"
        "/recommend - получить рекомендации\n"
        "/genres - выбрать любимые жанры"
    )

@dp.message_handler(commands=['rate'])
async def rate_book_start(message: types.Message):
    await BookRating.waiting_for_book_title.set()
    await message.answer("Напишите название книги, которую хотите оценить:")

@dp.message_handler(state=BookRating.waiting_for_book_title)
async def process_book_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['book_title'] = message.text
    
    await BookRating.next()
    await message.answer("Теперь оцените книгу от 1 до 5:")

@dp.message_handler(state=BookRating.waiting_for_rating)
async def process_rating(message: types.Message, state: FSMContext):
    try:
        rating = int(message.text)
        if rating < 1 or rating > 5:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите число от 1 до 5")
        return

    async with state.proxy() as data:
        book_title = data['book_title']
        user = get_or_create_user(message.from_user.id)
        user.preferences['rated_books'][book_title] = rating
        update_user_preferences(message.from_user.id, user.preferences)
    
    await state.finish()
    await message.answer(f"Спасибо! Вы оценили книгу '{book_title}' на {rating}")

@dp.message_handler(commands=['recommend'])
async def recommend_books(message: types.Message):
    recommendations = recommender.get_user_recommendations(message.from_user.id)
    response = "📚 Рекомендуемые книги:\n\n"
    for _, row in recommendations.iterrows():
        response += f"{row['title']} - {row['author']}\n"
    await message.answer(response)

@dp.message_handler(commands=['genres'])
async def show_genres(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Фантастика", "Фэнтези", "Детектив", "Роман")
    await message.answer("Выберите любимые жанры:", reply_markup=markup)

@dp.message_handler(lambda message: message.text in ["Фантастика", "Фэнтези", "Детектив", "Роман"])
async def add_genre(message: types.Message):
    user = get_or_create_user(message.from_user.id)
    if message.text not in user.preferences['genres']:
        user.preferences['genres'].append(message.text)
        update_user_preferences(message.from_user.id, user.preferences)
        await message.answer(f"Жанр '{message.text}' добавлен в ваши предпочтения")
    else:
        await message.answer(f"Жанр '{message.text}' уже в ваших предпочтениях")

if __name__ == '__main__':
    init_db()
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)