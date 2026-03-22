import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Settings(BaseSettings):
    MONGO_URI: str = os.getenv("MONGO_URI", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your_secret_key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_NAME: str = "dev_clash_db"
    
    # Keeping Gemini keys just in case you ever want to switch back
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", "./chroma_db")
    GEMINI_API_KEY_2: str = os.getenv("GEMINI_API_KEY_2", "")
    
    # 🔴 Added Groq Key
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY","")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# 🔴 Updated validation to ensure Groq is ready to go
if not settings.GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from environment variables or .env file.")