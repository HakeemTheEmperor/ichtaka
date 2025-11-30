from fastapi import Depends
from src.database import get_db

DB_SESSION = Depends(get_db)