import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from model import BookRecommender
from database import init_db, get_or_create_user, update_user_preferences

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

# Инициализация базы данных и модели (модель загружается/создается внутри BookRecommender)
init_db()
recommender = BookRecommender()

# # Проверка, существует ли файл модели
# model_path = 'data/model.joblib'
# if os.path.exists(model_path):
#     print("Загрузка существующей модели...")
#     # Загрузка модели и данных
#     try:
#         recommender.load_model(model_path)
#         print("Модель успешно загружена.")
#     except Exception as e:
#         print(f"Ошибка при загрузке модели: {e}")
#         # Если загрузка не удалась, можно попробовать пересоздать модель или выйти
#         # Пока оставим, чтобы бот мог запуститься даже без модели, но рекомендации не будут работать
# else:
#     print("Файл модели не найден. Запустите load_books.py для создания.")

print("Файл bot.py действительно запускается")

async def start(update: Update, context: CallbackContext):
    user = get_or_create_user(update.effective_user.id)
    welcome_message = (
        "👋 Привет! Я бот для рекомендации книг.\n\n"
        "Доступные команды:\n"
        "/recommend - Получить рекомендации\n"
        "/genre - Рекомендации по жанру\n"
        "/author - Рекомендации по автору\n"
        "/info - Информация о книге\n"
        "/rate - Оценить книгу\n"
        "/help - Помощь"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "📚 Список команд:\n\n"
        "/recommend - Получить персонализированные рекомендации\n"
        "/genre - Показать список жанров и получить рекомендации\n"
        "/author - Поиск книг по автору\n"
        "/info <название> - Получить информацию о книге\n"
        "/rate <название> - Оценить книгу (от 1 до 5)\n"
        "/help - Показать это сообщение"
    )
    await update.message.reply_text(help_text)

async def recommend(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_or_create_user(user_id)
    preferences = user['preferences']

    recommendations = []
    # Приоритет: понравившиеся книги -> любимые жанры -> случайные
    if preferences.get('liked_books'):
        # Берем последнюю понравившуюся книгу для рекомендации похожих
        last_liked_book_title = list(preferences['liked_books'].keys())[-1] if preferences['liked_books'] else None
        if last_liked_book_title:
            try:
                recommendations = recommender.recommend(last_liked_book_title)
            except ValueError:
                # Книга не найдена в базе для рекомендаций
                pass
    
    if not recommendations and preferences.get('genres'):
        # Берем последний выбранный жанр
        last_genre = preferences['genres'][-1] if preferences['genres'] else None
        if last_genre:
            recommendations = recommender.get_recommendations_by_genre(last_genre)

    # Если рекомендаций все еще нет, даем случайные
    if not recommendations:
        # Предполагается, что у recommender есть метод для случайных книг или можно получить из books_df
        # Здесь пример получения случайных из load_books.py, нужно адаптировать под ваш recommender
        try:
            # Пример: если recommender имеет доступ к books_df
            if hasattr(recommender, 'books_df') and recommender.books_df is not None:
                recommendations = recommender.books_df.sample(n=5).to_dict('records')
            # Иначе, возможно, нужно будет загрузить книги заново или добавить метод в recommender
            # recommendations = load_random_books(5) # Пример функции
            if not recommendations:
                await update.message.reply_text("К сожалению, не удалось найти рекомендации. Попробуйте оценить несколько книг.")
                return
        except Exception as e:
            print(f"Ошибка при получении случайных рекомендаций: {e}")
            await update.message.reply_text("Произошла ошибка при получении рекомендаций.")
            return

    if not recommendations:
        await update.message.reply_text("К сожалению, не удалось найти рекомендации. Попробуйте оценить несколько книг.")
        return
    
    message = "📚 Вот несколько книг, которые могут вам понравиться:\n\n"
    for book in recommendations:
        message += f"📖 {book['title']} - {book['author']}\n"
        message += f"⭐️ Рейтинг: {book['rating']}\n"
        message += f"📝 {book['description'][:200]}...\n\n"
    
    await update.message.reply_text(message)

async def show_genres(update: Update, context: CallbackContext):
    genres = recommender.get_all_genres()
    keyboard = []
    
    # Создаем кнопки по 2 в ряд
    for i in range(0, len(genres), 2):
        row = []
        row.append(InlineKeyboardButton(genres[i], callback_data=f"genre_{genres[i]}"))
        if i + 1 < len(genres):
            row.append(InlineKeyboardButton(genres[i + 1], callback_data=f"genre_{genres[i + 1]}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите жанр:", reply_markup=reply_markup)

async def show_authors(update: Update, context: CallbackContext):
    authors = recommender.get_all_authors()
    keyboard = []
    
    # Создаем кнопки по 2 в ряд
    for i in range(0, len(authors), 2):
        row = []
        row.append(InlineKeyboardButton(authors[i], callback_data=f"author_{authors[i]}"))
        if i + 1 < len(authors):
            row.append(InlineKeyboardButton(authors[i + 1], callback_data=f"author_{authors[i + 1]}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите автора:", reply_markup=reply_markup)

async def get_book_info(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите название книги: /info <название>")
        return
    
    book_title = " ".join(context.args)
    book_info = recommender.get_book_info(book_title)
    
    if not book_info:
        await update.message.reply_text("Книга не найдена. Проверьте название и попробуйте снова.")
        return
    
    message = (
        f"📖 {book_info['title']}\n"
        f"✍️ Автор: {book_info['author']}\n"
        f"📚 Жанр: {book_info['genre']}\n"
        f"⭐️ Рейтинг: {book_info['rating']}\n"
        f"📝 Описание: {book_info['description']}"
    )
    
    await update.message.reply_text(message)

async def rate_book(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        await update.message.reply_text("Пожалуйста, укажите название книги и оценку: /rate <название> <оценка>")
        return
    
    try:
        rating = int(context.args[-1])
    except ValueError:
        await update.message.reply_text("Оценка должна быть числом. Пожалуйста, укажите название книги и оценку: /rate <название> <оценка>")
        return

    if not 1 <= rating <= 5:
        await update.message.reply_text("Оценка должна быть от 1 до 5")
        return
    
    book_title = " ".join(context.args[:-1])
    book_info = recommender.get_book_info(book_title)
    
    if not book_info:
        await update.message.reply_text("Книга с таким названием не найдена. Пожалуйста, проверьте название и попробуйте снова.")
        return
    
    user_id = update.effective_user.id
    user = get_or_create_user(user_id)
    
    # Обновляем предпочтения пользователя
    if 'rated_books' not in user['preferences']:
        user['preferences']['rated_books'] = {}
    
    user['preferences']['rated_books'][book_title] = rating
    update_user_preferences(user_id, user['preferences'])
    
    await update.message.reply_text(f"Спасибо! Вы оценили книгу '{book_title}' на {rating}⭐")

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    print(f"Получен callback с данными: {data}")
    
    if data[0] == 'genre':
        genre = '_'.join(data[1:])
        print(f"Выбран жанр: {genre}")
        
        user_id = update.effective_user.id
        user = get_or_create_user(user_id)
        if 'genres' not in user['preferences']:
            user['preferences']['genres'] = []
        if genre not in user['preferences']['genres']:
            user['preferences']['genres'].append(genre)
        update_user_preferences(user_id, user['preferences'])
        
        recommendations = recommender.get_recommendations_by_genre(genre)
        print(f"Найдено рекомендаций: {len(recommendations)}")
        
        if not recommendations:
            await query.edit_message_text(f"К сожалению, не найдено книг в жанре {genre}")
            return
        
        message = f"📚 Книги в жанре {genre}:\n\n"
        for book in recommendations:
            message += f"📖 {book['title']} - {book['author']}\n"
            message += f"⭐️ Рейтинг: {book['rating']}\n"
            message += f"📝 {book['description'][:200]}...\n\n"
        
        await query.edit_message_text(message)
    
    elif data[0] == 'author':
        author = '_'.join(data[1:])
        recommendations = recommender.get_recommendations_by_author(author)
        
        if not recommendations:
            await query.edit_message_text(f"К сожалению, не найдено книг автора {author}")
            return
        
        message = f"📚 Книги автора {author}:\n\n"
        for book in recommendations:
            message += f"📖 {book['title']}\n"
            message += f"⭐️ Рейтинг: {book['rating']}\n"
            message += f"📝 {book['description'][:200]}...\n\n"
        
        await query.edit_message_text(message)

def main():
    # updater = Updater(TOKEN)
    # dp = updater.dispatcher

    application = ApplicationBuilder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("recommend", recommend))
    application.add_handler(CommandHandler("genre", show_genres))
    application.add_handler(CommandHandler("author", show_authors))
    application.add_handler(CommandHandler("info", get_book_info))
    application.add_handler(CommandHandler("rate", rate_book))
    
    # Добавляем обработчик callback-запросов
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Запуск бота
    application.run_polling()
    # updater.start_polling()
    # updater.idle()

if __name__ == '__main__':
    main()