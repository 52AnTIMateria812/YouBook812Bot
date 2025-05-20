import pandas as pd
import requests
import time
import random
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def get_books_from_openlibrary(query, limit=50):
    books = []
    base_url = "https://openlibrary.org/search.json"
    
    try:
        response = requests.get(base_url, params={'q': query, 'limit': limit})
        if response.status_code != 200:
            print(f"Ошибка при запросе к OpenLibrary: {response.status_code}")
            return books
            
        data = response.json()
        if not isinstance(data, dict) or 'docs' not in data:
            print(f"Неверный формат ответа от API")
            return books
        
        for doc in data.get('docs', []):
            try:
                if not isinstance(doc, dict):
                    continue
                    
                # Получаем дополнительную информацию о книге
                work_id = doc.get('key')
                if not work_id:
                    continue
                    
                work_url = f"https://openlibrary.org{work_id}.json"
                work_response = requests.get(work_url)
                if work_response.status_code != 200:
                    continue
                    
                work_data = work_response.json()
                if not isinstance(work_data, dict):
                    continue
                
                # Извлекаем жанры
                subjects = work_data.get('subjects', [])
                if not isinstance(subjects, list):
                    subjects = []
                genres = [s for s in subjects if isinstance(s, str) and len(s.split()) < 3]
                
                # Получаем описание
                description = ''
                if isinstance(work_data.get('description'), dict):
                    description = work_data['description'].get('value', '')
                elif isinstance(work_data.get('description'), str):
                    description = work_data['description']
                
                book = {
                    "title": doc.get('title', ''),
                    "author": doc.get('author_name', ['Неизвестен'])[0] if doc.get('author_name') else 'Неизвестен',
                    "rating": float(doc.get('ratings_average', 0) or 4.0),
                    "description": description,
                    "genre": genres[0] if genres else 'Не указан',
                    "genres": genres,
                    "cover_id": doc.get('cover_i'),
                    "first_publish_year": doc.get('first_publish_year'),
                    "edition_count": doc.get('edition_count', 0)
                }
                books.append(book)
                
            except Exception as e:
                print(f"Ошибка при обработке книги: {e}")
                continue
                
            time.sleep(0.5)  # Уважаем rate limits API
            
    except Exception as e:
        print(f"Ошибка при запросе к OpenLibrary: {e}")
    
    return books

class BookRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.books_df = None
        self.tfidf_matrix = None
        
    def fit(self, books):
        if not books:
            raise ValueError("Список книг пуст")
            
        self.books_df = pd.DataFrame(books)
        
        # Заполняем пропущенные значения
        self.books_df['description'] = self.books_df['description'].fillna('')
        self.books_df['genres'] = self.books_df['genres'].apply(lambda x: x if isinstance(x, list) else [])
        
        # Создаем текстовое представление книг для векторизации
        book_texts = self.books_df.apply(
            lambda x: f"{x['title']} {x['author']} {x['genre']} {' '.join(x['genres'])} {x['description']}", 
            axis=1
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(book_texts)
        
    def recommend(self, book_title, n_recommendations=5):
        if self.books_df is None or self.tfidf_matrix is None:
            raise ValueError("Модель не обучена. Сначала вызовите метод fit()")
            
        # Находим индекс книги
        book_idx = self.books_df[self.books_df['title'] == book_title].index
        if len(book_idx) == 0:
            return []
            
        # Вычисляем схожесть
        similarity_scores = cosine_similarity(self.tfidf_matrix[book_idx], self.tfidf_matrix).flatten()
        
        # Получаем индексы наиболее похожих книг
        similar_indices = similarity_scores.argsort()[::-1][1:n_recommendations+1]
        
        # Проверяем, что индексы не выходят за пределы
        similar_indices = similar_indices[similar_indices < len(self.books_df)]
        
        if len(similar_indices) == 0:
            return []
            
        return self.books_df.iloc[similar_indices].to_dict('records')

def main():
    print("Начинаем загрузку книг из OpenLibrary...")
    
    # Загружаем книги по разным жанрам
    genres = ['fantasy', 'science fiction', 'mystery', 'romance', 'classic']
    all_books = []
    
    for genre in genres:
        print(f"Загружаем книги жанра: {genre}")
        books = get_books_from_openlibrary(genre)
        all_books.extend(books)
        print(f"Загружено {len(books)} книг жанра {genre}")
    
    # Создаем и обучаем рекомендательную систему
    recommender = BookRecommender()
    recommender.fit(all_books)
    
    # Сохраняем данные
    df = pd.DataFrame(all_books)
    df.to_csv('data/books.csv', index=False)
    
    # Сохраняем статистику
    stats = {
        'total_books': len(df),
        'unique_authors': df['author'].nunique(),
        'unique_genres': df['genre'].nunique(),
        'average_rating': df['rating'].mean(),
        'genres_distribution': df['genre'].value_counts().to_dict()
    }
    
    with open('data/stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)
    
    print("\nСтатистика базы данных:")
    print(f"Всего книг: {stats['total_books']}")
    print(f"Уникальных авторов: {stats['unique_authors']}")
    print(f"Уникальных жанров: {stats['unique_genres']}")
    print(f"Средний рейтинг: {stats['average_rating']:.2f}")

if __name__ == "__main__":
    main() 