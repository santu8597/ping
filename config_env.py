from decouple import config, Csv
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Security Settings
    HOST_URL = config('HOST_URL', default='http://localhost:8000')
    ALLOWED_HOST = config('ALLOWED_HOST', default='localhost').split(',')
    CORS_ORIGIN_WHITELIST = config('CORS_ORIGIN_WHITELIST').split(',')
    CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS').split(',')
    API_URL_VIZ = config('API_URL_VIZ')
    API_URL_RD3 = config('API_URL_RD3')
    APIKEY = config('APIKEY')
    
    #Gemini API Key
    GEMINI_API_KEY = config('GEMINI_API_KEY')
    OPENAI_API_KEY = config('OPENAI_API_KEY')
    ACTIVE_API = config('ACTIVE_API')
    DEBUG = config('DEBUG', default=False, cast=bool)

    # Email Settings
    EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='your-email@gmail.com')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='your-app-password')
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='no-reply@example.com')
    EMAIL_SERVER = config('EMAIL_SERVER', default='SMTP')
    SMTP_FROM = config('SMTP_FROM', default='smtp.gmail.com')
    SENDGRID_API_KEY = config('SENDGRID_API_KEY')

    # Twilio Settings (For Mobile)
    TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN')
    TWILIO_VERIFY_SERVICE_SID = config('TWILIO_VERIFY_SERVICE_SID')

    # Redis Configuration
    REDIS_DEFAULT_URL = config('REDIS_DEFAULT_URL')
    REDIS_OTP_URL = config('REDIS_OTP_URL')
    REDIS_SESSION_URL = config('REDIS_SESSION_URL')
    REDIS_AI_SUMMARY_URL=config('REDIS_AI_SUMMARY_URL')
    REDIS_ROOT_SERVER_URL = config('REDIS_ROOT_SERVER_URL')
    REDIS_IP_URL = config('REDIS_IP_URL')

    # Database Configuration
    DB_NAME = config('DB_NAME', default='projectdb')
    DB_USER = config('DB_USER', default='postgres')
    DB_PASSWORD = config('DB_PASSWORD', default='your_database_password')
    DB_HOST = config('DB_HOST', default='localhost')
    DB_PORT = config('DB_PORT', default=5432, cast=int)

    # S3 Configuration
    DEFAULT_FILE_STORAGE = config('DEFAULT_FILE_STORAGE')

    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME')
    AWS_S3_ADDRESSING_STYLE = config('AWS_S3_ADDRESSING_STYLE')

    ROOT_VIZ_URL = config('ROOT_VIZ_URL')

    IPINFO_TOKEN_NEW=config('IPINFO_TOKEN_NEW')

    MEASUREMENT_ANCHOR_IDS=config('MEASUREMENT_ANCHOR_IDS').split(',')


CONFIG = Settings()

