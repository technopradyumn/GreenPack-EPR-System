from pydantic_settings import BaseSettings


import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "greenpack"

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    GEMINI_API_KEY: str | None = None

    class Config:
        env_file = os.path.join(BASE_DIR, ".env")


settings = Settings()