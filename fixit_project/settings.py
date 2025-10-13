"""Django settings for fixit_project project."""
import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = []
# Application definition
INSTALLED_APPS = [
 'django.contrib.admin',
 'django.contrib.auth',
 'django.contrib.contenttypes',
 'django.contrib.sessions',
 'django.contrib.messages',
 'django.contrib.staticfiles',
 'accounts', # Our custom app
]
MIDDLEWARE = [
 'django.middleware.security.SecurityMiddleware',
 'django.contrib.sessions.middleware.SessionMiddleware',
 'django.middleware.common.CommonMiddleware',
 'django.middleware.csrf.CsrfViewMiddleware',
 'django.contrib.auth.middleware.AuthenticationMiddleware',
 'django.contrib.messages.middleware.MessageMiddleware',
 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'fixit_project.urls'
TEMPLATES = [
 {
 'BACKEND': 'django.template.backends.django.DjangoTemplates',
 'DIRS': [os.path.join(BASE_DIR, 'templates')],
 'APP_DIRS': True,
 'OPTIONS': {
 'context_processors': [
 'django.template.context_processors.debug',
 'django.template.context_processors.request',
 'django.contrib.auth.context_processors.auth',
 'django.contrib.messages.context_processors.messages',
 ],
 },
 },
]
WSGI_APPLICATION = 'fixit_project.wsgi.application'
# Database - PostgreSQL (Supabase)
DATABASES = {
 'default': {
 'ENGINE': 'django.db.backends.postgresql',
 'NAME': config('DB_NAME'),
 'USER': config('DB_USER'),
 'PASSWORD': config('DB_PASSWORD'),
 'HOST': config('DB_HOST'),
 'PORT': config('DB_PORT'),
 }
}
# Password validation
AUTH_PASSWORD_VALIDATORS = [
 {
 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
 },
 {
 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
 },
 {
 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
 },
 {
 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
 },
]
# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila' # Philippines timezone
USE_I18N = True
USE_TZ = True
# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Authentication redirects
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'