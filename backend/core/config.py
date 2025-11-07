# Configuration settings for the Smart Vehicle License Scanner
# Centralized configuration management using Pydantic Settings

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All sensitive values should be set via environment variables in production.
    """
    
    # Application Settings
    APP_NAME: str = "Smart Vehicle License Scanner"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database Settings
    DATABASE_URL: str = "postgresql://sva_user:sva_password@localhost:5432/license_scanner"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    
    # File Storage Settings
    UPLOAD_DIR: str = "data/uploads"
    MODELS_DIR: str = "models"
    LOGS_DIR: str = "logs"
    
    # Image Processing Settings
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    SUPPORTED_IMAGE_FORMATS: List[str] = ["jpg", "jpeg", "png", "bmp", "tiff"]
    
    # License Plate Detection Settings
    PLATE_DETECTION_CONFIDENCE: float = 0.6
    OCR_CONFIDENCE_THRESHOLD: float = 0.45
    MAX_PLATE_LENGTH: int = 10
    MIN_PLATE_LENGTH: int = 4
    
    # Camera Settings
    DEFAULT_FPS: int = 25
    FRAME_BUFFER_SIZE: int = 100
    RTSP_TIMEOUT: int = 30
    FRAME_SKIP: int = 2
    
    # Security & Privacy Settings
    PLATE_HASH_SALT: str = "your-plate-hash-salt-change-in-production"
    ENABLE_PLATE_HASHING: bool = True
    STORE_PLATE_THUMBNAILS: bool = True
    
    # Performance Settings
    MAX_CONCURRENT_PROCESSING: int = 4
    PROCESSING_TIMEOUT: int = 30
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Ensure required directories exist
def ensure_directories():
    """
    Create necessary directories if they don't exist.
    """
    directories = [
        settings.UPLOAD_DIR,
        settings.MODELS_DIR,
        settings.LOGS_DIR,
        "data/processed",
        "data/exports"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Initialize directories on import
ensure_directories()
