import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Security Configuration
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set in environment variables")
    
    WTF_CSRF_SECRET_KEY = os.getenv('WTF_CSRF_SECRET_KEY')
    if not WTF_CSRF_SECRET_KEY:
        raise ValueError("No WTF_CSRF_SECRET_KEY set in environment variables")
    
    # PostgreSQL Database Config
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("No DATABASE_URL set in environment variables")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join('public', 'uploads'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # Default 16MB
    
    # Admin registration
    ADMIN_REGISTRATION_KEY = os.getenv('ADMIN_REGISTRATION_KEY')
    if not ADMIN_REGISTRATION_KEY:
        raise ValueError("No ADMIN_REGISTRATION_KEY set in environment variables")
    ALLOW_ADMIN_REGISTRATION = os.getenv('ALLOW_ADMIN_REGISTRATION', 'false').lower() == 'true' 