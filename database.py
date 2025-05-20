import sqlite3
import json
from typing import Dict, Any

def init_db():
    conn = sqlite3.connect('data/books.db')
    c = conn.cursor()
    
    # Создаем таблицу пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            preferences TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_or_create_user(user_id: int) -> Dict[str, Any]:
    conn = sqlite3.connect('data/books.db')
    c = conn.cursor()
    
    # Получаем пользователя
    c.execute('SELECT preferences FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    
    if result:
        preferences = json.loads(result[0])
    else:
        # Создаем нового пользователя
        preferences = {
            'rated_books': {},
            'genres': []
        }
        c.execute(
            'INSERT INTO users (user_id, preferences) VALUES (?, ?)',
            (user_id, json.dumps(preferences))
        )
        conn.commit()
    
    conn.close()
    return {'user_id': user_id, 'preferences': preferences}

def update_user_preferences(user_id: int, preferences: Dict[str, Any]):
    conn = sqlite3.connect('data/books.db')
    c = conn.cursor()
    
    c.execute(
        'UPDATE users SET preferences = ? WHERE user_id = ?',
        (json.dumps(preferences), user_id)
    )
    
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('data/books.db')
    c = conn.cursor()
    
    c.execute('SELECT user_id, preferences FROM users')
    users = []
    for user_id, preferences in c.fetchall():
        users.append({
            'user_id': user_id,
            'preferences': json.loads(preferences)
        })
    
    conn.close()
    return users