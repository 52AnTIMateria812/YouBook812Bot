import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import os
from database import get_or_create_user

class BookRecommender:
    def __init__(self):
        self.books_df = None
        self.tfidf_matrix = None
        self.vectorizer = None
        self.model_path = 'data/model.joblib'
        self.load_or_create_model()

    def load_or_create_model(self):
        if os.path.exists(self.model_path):
            print("Загрузка существующей модели...")
            try:
                self.books_df, self.tfidf_matrix, self.vectorizer = joblib.load(self.model_path)
                # Проверяем наличие необходимых колонок
                if 'clean_title' not in self.books_df.columns:
                    print("Пересоздание модели из-за отсутствия необходимых колонок...")
                    self.create_model()
                else:
                    print("Модель успешно загружена.")
            except Exception as e:
                print(f"Ошибка при загрузке модели: {e}")
                print("Пересоздание модели...")
                self.create_model()
        else:
            print("Создание новой модели...")
            self.create_model()

    def create_model(self):
        # Загрузка данных
        self.books_df = pd.read_csv('data/books.csv')
        
        # Создаем колонку для удобного поиска без учета регистра и лишних пробелов
        self.books_df['clean_title'] = self.books_df['title'].str.lower().str.strip()
        print("Примеры clean_title после создания модели:")
        print(self.books_df['clean_title'].head())
        
        # Создание текстового описания для каждой книги
        self.books_df['content'] = self.books_df.apply(
            lambda x: f"{x['title']} {x['author']} {x['genre']} {x['description']}", 
            axis=1
        )
        
        # Создание TF-IDF матрицы
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2)
        )
        
        self.tfidf_matrix = self.vectorizer.fit_transform(self.books_df['content'])
        
        # Сохранение модели
        joblib.dump((self.books_df, self.tfidf_matrix, self.vectorizer), self.model_path)

    def get_recommendations(self, book_title, n_recommendations=5):
        # Поиск индекса книги
        book_idx = self.books_df[self.books_df['title'].str.lower() == book_title.lower()].index
        
        if len(book_idx) == 0:
            return []
        
        book_idx = book_idx[0]
        
        # Вычисление косинусного сходства
        cosine_similarities = cosine_similarity(
            self.tfidf_matrix[book_idx:book_idx+1], 
            self.tfidf_matrix
        ).flatten()
        
        # Получение индексов похожих книг
        similar_indices = cosine_similarities.argsort()[::-1][1:n_recommendations+1]
        
        # Формирование рекомендаций
        recommendations = []
        for idx in similar_indices:
            book = self.books_df.iloc[idx]
            recommendations.append({
                'title': book['title'],
                'author': book['author'],
                'genre': book['genre'],
                'rating': book['rating'],
                'description': book['description'],
                'similarity_score': cosine_similarities[idx]
            })
        
        return recommendations

    def get_recommendations_by_genre(self, genre, n_recommendations=5):
        # Фильтрация книг по жанру
        genre_books = self.books_df[self.books_df['genre'].str.lower().str.contains(genre.lower(), na=False)]
        
        if len(genre_books) == 0:
            return []
        
        # Сортировка по рейтингу
        top_books = genre_books.nlargest(n_recommendations, 'rating')
        
        recommendations = []
        for _, book in top_books.iterrows():
            recommendations.append({
                'title': book['title'],
                'author': book['author'],
                'genre': book['genre'],
                'rating': book['rating'],
                'description': book['description']
            })
        
        return recommendations

    def get_recommendations_by_author(self, author, n_recommendations=20):
        author_books = self.find_books_by_author(author)
        
        if len(author_books) == 0:
            return []
        
        # Сортировка по названию и выбор первых N
        sorted_books = author_books.sort_values(by='title')
        top_books = sorted_books.head(n_recommendations)
        
        recommendations = []
        for _, book in top_books.iterrows():
            recommendations.append({
                'title': book['title'],
                'author': book['author'],
                'genre': book['genre'],
                'rating': book['rating'],
                'description': book['description']
            })
        
        return recommendations

    def get_all_genres(self):
        return sorted(self.books_df['genre'].unique())

    def get_all_authors(self):
        # Получаем всех авторов
        authors = self.books_df['author'].unique()
        
        # Нормализуем имена авторов
        normalized_authors = {}
        for author in authors:
            # Приводим к нижнему регистру и убираем лишние пробелы
            normalized = author.lower().strip()
            # Если такого автора еще нет в словаре, добавляем его
            if normalized not in normalized_authors:
                normalized_authors[normalized] = author
        
        # Возвращаем оригинальные имена авторов (не нормализованные)
        return sorted(normalized_authors.values())

    def get_book_info(self, book_title):
        # Ищем по частичному совпадению подстроки в 'clean_title'
        clean_input_title = book_title.lower().strip()
        # Используем str.contains для поиска подстроки
        book = self.books_df[self.books_df['clean_title'].str.contains(clean_input_title, na=False)]
        
        if len(book) == 0:
            return None
        
        book = book.iloc[0]
        return {
            'title': book['title'],
            'author': book['author'],
            'genre': book['genre'],
            'rating': book['rating'],
            'description': book['description']
        }

    # Вспомогательная функция для поиска книг автора (используется в рекомендациях по автору)
    def find_books_by_author(self, author_name):
        # Поиск автора с точным совпадением (без учета регистра)
        author_books = self.books_df[self.books_df['author'].str.lower() == author_name.lower()]
        return author_books

    def get_user_recommendations(self, user_id):
        user = get_or_create_user(user_id)
        rated_books = user.preferences.get('rated_books', {})
        
        if not rated_books:
            return self.books_df.sample(3)[['title', 'author']]
            
        # Простая гибридная рекомендация (можно заменить на более сложную логику)
        last_rated = list(rated_books.keys())[-1]
        return self.get_recommendations(last_rated)