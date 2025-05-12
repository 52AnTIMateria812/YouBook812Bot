import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database import get_or_create_user
import numpy as np

class BookRecommender:
    def __init__(self, data_path='data/books.csv'):
        self.df = pd.read_csv(data_path)
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['description'].fillna(''))
        
    def get_content_based_recommendations(self, book_title, n=5):
        idx = self.df[self.df['title'] == book_title].index[0]
        sim_scores = cosine_similarity(self.tfidf_matrix[idx], self.tfidf_matrix)
        sim_scores = sim_scores.flatten()
        similar_indices = np.argsort(sim_scores)[-n-1:-1][::-1]
        return self.df.iloc[similar_indices][['title', 'author']]
    
    def get_user_recommendations(self, user_id):
        user = get_or_create_user(user_id)
        rated_books = user.preferences.get('rated_books', {})
        
        if not rated_books:
            return self.df.sample(3)[['title', 'author']]
            
        # Простая гибридная рекомендация (можно заменить на более сложную логику)
        last_rated = list(rated_books.keys())[-1]
        return self.get_content_based_recommendations(last_rated)