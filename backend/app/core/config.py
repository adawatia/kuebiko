import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/comics")
    SECRET_KEY = os.getenv("SECRET_KEY", "SECRET")


settings = Settings()
