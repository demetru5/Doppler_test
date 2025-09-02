import os

# Development-specific settings
class DevelopmentConfig:
    # Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    DEBUG = True
    TESTING = False
    
    # Server settings
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # CORS settings
    CORS_ORIGINS = "*"
    
    # Moomoo settings
    MOOMOO_HOST = '69.197.187.190'
    MOOMOO_PORT1 = 8080
    
    # Polygon API settings
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

    # Database settings
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'local')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'local_password')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'doppler-db')

    # Redis settings (for SocketIO)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Security settings (relaxed for development)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate limiting (disabled for development)
    RATELIMIT_ENABLED = False 