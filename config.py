import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'multilingual-resource-translation-key-2026')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Upload configurations
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'pdf'}
    
    # Database configuration
    DATABASE_PATH = os.path.join(BASE_DIR, 'translation_system.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    
    # Tesseract standard path for Windows
    TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    @classmethod
    def init_app(cls):
        # Create upload folder if not exists
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
