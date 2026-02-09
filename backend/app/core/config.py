import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/kuebiko_db")
    SECRET_KEY = os.getenv("SECRET_KEY", "SECRET")
    
    # Supabase Storage Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "comics")


settings = Settings()
