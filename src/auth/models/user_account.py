from sqlalchemy import Column, String, BigInteger, JSON
from src.database import Base

class User_Account(Base):
    __tablename__ = "user_account"
    
    id = Column(BigInteger, primary_key=True, index=True)
    login_id = Column(String, unique=True, index=True, nullable=False)  # system-generated
    public_key = Column(String, nullable=False)  # Ed25519 public key (base64)
    current_challenge = Column(String, nullable=True)  # Store active challenge for verification
    recovery_phrase_hashes = Column(JSON, nullable=False)  # list of 20 hashed words
    pseudonym = Column(String, unique=True, nullable=False)
    
    from sqlalchemy.orm import relationship
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    