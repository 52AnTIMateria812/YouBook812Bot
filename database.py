from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()
engine = create_engine(os.getenv('DATABASE_URL'))
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    preferences = Column(JSON)  # {'genres': [], 'rated_books': {}}
    
    def __repr__(self):
        return f"<User(user_id={self.user_id})>"

def init_db():
    Base.metadata.create_all(engine)

def get_or_create_user(user_id):
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        user = User(user_id=user_id, preferences={'genres': [], 'rated_books': {}})
        session.add(user)
        session.commit()
    return user

def update_user_preferences(user_id, preferences):
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if user:
        user.preferences = preferences
        session.commit()
    return user