from sqlalchemy import Column, Integer, String
from src.database import Base

class User_Account(Base):
    __tablename__ = "user_account"
    id = Column(Integer, primary_key=True, index=True)
    
    public_key = Column(String, unique=True, index=True, nullable=False)
    
    user_name = Column(String, unique=True, nullable=False)
    key_algorithm = Column(String, default="Ed25519", nullable=False)
    current_challenge = Column(String, nullable=True)
    