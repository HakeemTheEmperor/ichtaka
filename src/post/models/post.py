from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from src.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    file_url = Column(String, nullable=True)
    file_type = Column(String, nullable=True)  # image | video | file

    severity = Column(String(20), nullable=False)
    location = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
