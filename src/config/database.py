from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_URI = os.getenv("DB_URI")

engine = create_engine(DB_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TodoItem(Base):
    __tablename__ = "todos"
    
    id = Column(Integer, primary_key=True)
    userId = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending", index=True)  # pending, done, cancelled, overdue
    priority = Column(String, default="medium", index=True)  # low, medium, high
    deadline = Column(DateTime, nullable=True, index=True)
    category = Column(String, default="personal", index=True) # personal, work, study
    createdAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updatedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

def create_tables():
    Base.metadata.create_all(bind=engine)
    
    # Create composite indexes for common query patterns
    Index('idx_user_status', TodoItem.userId, TodoItem.status)
    Index('idx_user_created', TodoItem.userId, TodoItem.createdAt)
    Index('idx_status_deadline', TodoItem.status, TodoItem.deadline)
    Index('idx_user_priority', TodoItem.userId, TodoItem.priority)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
