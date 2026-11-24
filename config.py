import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-development-secret-before-use')
    DEBUG = os.getenv('FLASK_DEBUG', '0').lower() in {'1','true','yes'}
    # SQLite gives a zero-configuration local preview. Set DATABASE_URL in .env
    # to the MySQL URL for the project's recommended/final database backend.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///campus_radio_manager.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle': 280}
    MAX_CONTENT_LENGTH = 12 * 1024 * 1024
    UPLOAD_FOLDER = str(BASE_DIR / 'uploads')
    EXPORT_FOLDER = str(BASE_DIR / 'exports')
    SAMPLE_DATA_FOLDER = str(BASE_DIR / 'sample_data' / 'team_e037')
    WTF_CSRF_TIME_LIMIT = 3600
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
