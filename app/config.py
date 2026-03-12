from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    
    # JWT Configuration
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Email Configuration (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Tech Nova"
    
    # Application URLs
    app_domain: str = "http://localhost:3000"
    
    # Application Configuration
    app_name: str = "Tech Nova API"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
