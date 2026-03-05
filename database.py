from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Настройка базы данных SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./advertisements.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Модель User
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")  # 'user' or 'admin'
    created_at = Column(DateTime, default=datetime.utcnow)

    advertisements = relationship("Advertisement", back_populates="owner")

# Модель Advertisement
class Advertisement(Base):
    __tablename__ = "advertisements"

    id = Column(Integer, primary_key=True, index=True)  # int с автоинкрементом
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="advertisements")

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
