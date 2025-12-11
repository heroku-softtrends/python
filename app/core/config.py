import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Environment configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development, production
    
    # Database URLs
    POSTGRES_URL: str = os.getenv("POSTGRES_URL", "postgresql://u5hihvko57gqfc:p5ea23a8e2d8fa635303f78804905693f10fd3afd70e7ea20ceba27019e82fdf1@c57oa7dm3pc281.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d22ec8obdr7dh")
    SQLITE_URL: str = os.getenv("SQLITE_URL", "sqlite:///./invoicereader.db")
    
    # Legacy DATABASE_URL for backward compatibility
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./invoicereader.db")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    # File upload settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads/")
    ALLOWED_EXTENSIONS: set = {"pdf"}
    
    # CORS settings
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # AI Model settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    
    # AWS S3 settings
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_S3_BUCKET_NAME: str = os.getenv("AWS_S3_BUCKET_NAME", "")
    
    # File storage mode - 'local' or 's3'
    FILE_STORAGE_MODE: str = os.getenv("FILE_STORAGE_MODE", "s3" if ENVIRONMENT == "production" else "local")

settings = Settings()