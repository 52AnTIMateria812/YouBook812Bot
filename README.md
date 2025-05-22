# YouBook812Bot

Telegram бот для рекомендации книг с использованием машинного обучения.

## Возможности

- 📚 Персонализированные рекомендации книг
- 🎯 Рекомендации по жанрам
- 👤 Рекомендации по авторам
- ⭐ Оценка книг
- 📖 Подробная информация о книгах
- 🔄 Обучение на основе оценок пользователей

## Установка

1. Клонируйте репозиторий:
```bash
git clone [https://github.com/52AnTIMateria812/YouBook812Bot/tree/beta.git]
cd YouBook812Bot
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

**В случае проблем с версиями библиотек (например, InconsistentVersionWarning):**
   a. Удалите файл `data/model.joblib` вручную или с помощью команды:
      ```bash
      python -c "import os; os.remove('data/model.joblib') if os.path.exists('data/model.joblib') else print('Файл не найден')"
      ```
   b. Повторно запустите скрипт загрузки данных для пересоздания модели:
      ```bash
      python data/load_books.py
      ```

4. Создайте файл `.env` в корневой директории и добавьте токен бота:
```
BOT_TOKEN=your_bot_token_here
```

5. Загрузите базу данных книг:
```bash
python data/load_books.py
```

## Запуск

```bash
python bot.py
```

## Использование

1. Найдите бота в Telegram по имени [@YouBook812Bot]
2. Отправьте команду `/start` для начала работы
3. Используйте следующие команды:
   - `/recommend` - получить персонализированные рекомендации
   - `/genre` - выбрать жанр и получить рекомендации
   - `/author` - выбрать автора и получить рекомендации
   - `/info <название>` - получить информацию о книге
   - `/rate <название> <оценка>` - оценить книгу (от 1 до 5)
   - `/help` - показать справку

## Структура проекта

```
YouBook812Bot-alpha/
├── bot.py              # Основной файл бота
├── model.py            # Модель рекомендаций
├── database.py         # Работа с базой данных
├── requirements.txt    # Зависимости
├── .env               # Конфигурация
└── data/
    ├── books.csv      # База данных книг
    ├── books.db       # База данных пользователей
    ├── load_books.py  # Скрипт загрузки книг
    └── model.joblib   # Сохраненная модель
```

## Технологии

- Python 3.13
- python-telegram-bot
- scikit-learn
- pandas
- numpy
- SQLite

