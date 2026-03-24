from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Supabase settings
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    
    # Paystack settings
    PAYSTACK_SECRET_KEY: str = ""
    PAYSTACK_WEBHOOK_SECRET: str = ""
    
    # Frontend URL for CORS
    FRONTEND_URL: str = "http://localhost:3000"
    
    # API settings
    API_URL: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()