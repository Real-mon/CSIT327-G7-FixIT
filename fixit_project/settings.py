# """
# Django settings for fixit_project project.
# """
# import os
# from pathlib import Path
# from decouple import config
# import django.conf
# import django.core.files.storage
# from urllib.parse import urlparse
# from dotenv import load_dotenv
# import dj_database_url

# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent

# # Load .env in local dev only (Render sets RENDER=true in production)
# if os.environ.get("RENDER", "") != "true":
#     load_dotenv()

# # SECURITY WARNING: keep the secret key used in production secret!
# # Use environment variable for Render, fallback to python-decouple for local dev
# SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", config('SECRET_KEY', default='unsafe-dev-key'))

# # SECURITY WARNING: don't run with debug turned on in production!
# # Use environment variable for Render, fallback to python-decouple for local dev
# DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true" or config('DEBUG', default=False, cast=bool)

# # ALLOWED_HOSTS - use environment variable for production, fallback to local hosts
# ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]
# if not ALLOWED_HOSTS:  # Fallback for local development
#     ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0']

# # CSRF_TRUSTED_ORIGINS - use environment variable for production
# CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

# # Application definition
# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'storages',  # For handling media files with cloud storage
#     'accounts',  # Our custom app
# ]

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     "whitenoise.middleware.WhiteNoiseMiddleware",  # <-- WhiteNoise for static files
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# ROOT_URLCONF = 'fixit_project.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [os.path.join(BASE_DIR, 'templates')],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#                 # Add this to access MEDIA_URL in templates
#                 'django.template.context_processors.media',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'fixit_project.wsgi.application'

# # Database configuration - Use DATABASE_URL for production, fallback to individual config for local
# DATABASE_URL = os.environ.get("DATABASE_URL")
# if DATABASE_URL:
#     # Use dj-database-url for production (Render + Supabase)
#     DATABASES = {
#         "default": dj_database_url.config(
#             default=DATABASE_URL,
#             conn_max_age=600,
#             ssl_require=True
#         )
#     }
# else:
#     # Fallback to individual database config for local development
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': config('DB_NAME'),
#             'USER': config('DB_USER'),
#             'PASSWORD': config('DB_PASSWORD'),
#             'HOST': config('DB_HOST'),
#             'PORT': config('DB_PORT'),
#             'OPTIONS': {'sslmode': 'require'}
#         },
#     }

# # Password validation
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]

# # Internationalization
# LANGUAGE_CODE = 'en-us'
# TIME_ZONE = 'Asia/Manila'  # Philippines timezone
# USE_I18N = True
# USE_TZ = True

# # Static files (CSS, JavaScript, Images)
# STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# # Enable WhiteNoise for static files in production
# if os.environ.get("RENDER", "") == "true":
#     STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# # Security (production)
# if os.environ.get("RENDER", "") == "true":
#     SECURE_SSL_REDIRECT = True
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True

# # Media files (User uploaded files like profile pictures)
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# FILE_UPLOAD_PERMISSIONS = 0o644  # Set file upload permissions

# # Default primary key field type
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# # Authentication redirects
# LOGIN_URL = 'login'
# LOGIN_REDIRECT_URL = 'dashboard'
# LOGOUT_REDIRECT_URL = 'login'

# # Supabase configuration - use environment variables or fallback to config
# SUPABASE_URL = os.environ.get("SUPABASE_URL", config('SUPABASE_URL', default=''))
# SUPABASE_KEY = os.environ.get("SUPABASE_KEY", config('SUPABASE_KEY', default=''))

# # File storage configuration
# DEFAULT_FILE_STORAGE = 'storages.backends.s3.S3Storage'

# STORAGES = {
#     "default": {
#         "BACKEND": "storages.backends.s3.S3Storage",
#     },
#     "staticfiles": {
#         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" if os.environ.get("RENDER", "") == "true" else "django.contrib.staticfiles.storage.StaticFilesStorage",
#     },
# }

# # Supabase Storage Configuration
# AWS_ACCESS_KEY_ID = os.environ.get("SUPABASE_S3_ACCESS_KEY", config('SUPABASE_S3_ACCESS_KEY', default=''))
# AWS_SECRET_ACCESS_KEY = os.environ.get("SUPABASE_S3_SECRET_KEY", config('SUPABASE_S3_SECRET_KEY', default=''))
# AWS_STORAGE_BUCKET_NAME = 'profile-pictures'
# AWS_S3_ENDPOINT_URL = 'https://gpxaxqghnwguwgpackig.storage.supabase.co/storage/v1/s3'
# AWS_S3_CUSTOM_DOMAIN = f"{os.environ.get('SUPABASE_PROJECT_REF', config('SUPABASE_PROJECT_REF', default=''))}.supabase.co/storage/v1/object/public/profile-pictures"
# AWS_S3_REGION_NAME = 'ap-south-1'  # Adjust based on your Supabase region
# AWS_S3_ADDRESSING_STYLE = 'path'
# AWS_S3_FILE_OVERWRITE = False
# AWS_DEFAULT_ACL = 'public-read'
# AWS_QUERYSTRING_AUTH = False
# AWS_S3_OBJECT_PARAMETERS = {
#     'CacheControl': 'max-age=86400',
# }
# AWS_S3_SIGNATURE_VERSION = 's3v4'
# AWS_S3_FILE_OVERWRITE = False

"""
Django settings for gather_ed project.
"""
 
import os
from pathlib import Path
import dj_database_url
from django.contrib import staticfiles
from dotenv import load_dotenv
 
# Load environment variables from .env (for local dev)
load_dotenv()
 
# =====================
# PATHS
# =====================
BASE_DIR = Path(__file__).resolve().parent.parent
 
# =====================
# SECURITY & DEBUG
# =====================
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-here')
 
# DEBUG is False by default unless explicitly set to True
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
 
ALLOWED_HOSTS = [
    'csit327-g7-fixit-xdl5.onrender.com',
    'localhost',
    '127.0.0.1',
]
 
# Add Render’s dynamic hostname if available
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
 
# =====================
# APPLICATIONS
# =====================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
 
    # Your apps
    'storages',
    'accounts',
]
 
# =====================
# MIDDLEWARE
# =====================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # for static files on Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
 
ROOT_URLCONF = 'fixit_project.urls'
 
# =====================
# TEMPLATES
# =====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
            'debug': DEBUG,  # auto-disable in production
        },
    },

]
 
WSGI_APPLICATION = 'fixit_project.wsgi.application'
 
# =====================
# DATABASE (Supabase)
# =====================
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=60,
        ssl_require=False,
    )
}
 
# =====================
# PASSWORD VALIDATION
# =====================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
 
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
 
# =====================
# INTERNATIONALIZATION
# =====================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
 
# =====================
# STATIC & MEDIA FILES
# =====================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
 
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
 

 
# =====================
# SUPABASE KEYS
# =====================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
 
if not SUPABASE_URL:
    print("⚠️ WARNING: SUPABASE_URL missing in environment variables.")
 
# =====================
# SESSION SECURITY & CONFIGURATION (6 HOURS)
# =====================
SESSION_COOKIE_HTTPONLY = True      # JS can't read session cookies
SESSION_COOKIE_SAMESITE = 'Lax'     # Protects against CSRF
SESSION_COOKIE_AGE = 6 * 60 * 60    # 6 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
 
# Secure cookies only in production
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
 
# =====================
# PERFORMANCE OPTIMIZATIONS
# =====================
WHITENOISE_MAX_AGE = 31536000  # 1 year cache
CONN_MAX_AGE = 60
WHITENOISE_USE_FINDERS = True
 
# =====================
# DEFAULT PRIMARY KEY
# =====================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'