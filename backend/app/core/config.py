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
    
    # Email settings
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@surepay.link"
    EMAIL_FROM_NAME: str = "SurePay"
    
    # Admin settings
    DEFAULT_ADMIN_EMAIL: str = "admin@surepay.link"
    DEFAULT_ADMIN_PASSWORD: str = "Admin123!"  # This should be changed in production
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()