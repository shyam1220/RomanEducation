import os

class Config:
    """Base configuration class."""
    # Database settings
    DB_HOST = os.environ.get('localhost')
    DB_USER = os.environ.get('root')
    DB_PASSWORD = os.environ.get('')
    DB_NAME = os.environ.get('course_registration')
    
    # SMTP settings
    SMTP_SERVER = os.environ.get('smtp.gmail.com')
    SMTP_PORT = 587
    SMTP_USERNAME = os.environ.get('varadharaj160@gmail.com')
    SMTP_PASSWORD = os.environ.get('jlsbkoanclltyfdy')
    ADMIN_EMAIL = os.environ.get('serankesavan@gmail.com') 
    
    # Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-for-sessions')
    
    # Razorpay settings
    RAZORPAY_KEY_ID = os.environ.get('rzp_test_JkbAxq5JbkMpIB')
    RAZORPAY_KEY_SECRET = os.environ.get('B8lCButNGCldzgnZ6MYI25Mb')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

# Default to development configuration
environment = os.environ.get('FLASK_ENV', 'development')

# Select the appropriate configuration based on environment
if environment == 'production':
    app_config = ProductionConfig()
else:
    app_config = DevelopmentConfig()



