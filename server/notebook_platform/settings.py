import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

env_path = Path('.') / '.env.dev'
load_dotenv(dotenv_path=env_path)

# ----------------------------------- Helper Functions -----------------------------------
def get_env_variable(var_name):
    """Get the environment variable or return an ImproperlyConfigured exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        raise ImproperlyConfigured(f"CRITICAL: The {var_name} environment variable is missing.")

# ----------------------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# --- Strictly Required Settings ---
SECRET_KEY = get_env_variable('DJANGO_SECRET_KEY')
WORKER_CALLBACK_URL = get_env_variable('WORKER_CALLBACK_URL')
CELERY_BROKER_URL = get_env_variable('CELERY_BROKER_URL')
WORKER_WEBHOOK_SECRET = get_env_variable('WORKER_WEBHOOK_SECRET')
WORKER_IMAGE = get_env_variable('WORKER_IMAGE')
AWS_BATCH_TRIGGER_FUNCTION = os.getenv('AWS_BATCH_TRIGGER_FUNCTION', 'lifewatch-batch-trigger')
AWS_BATCH_TRIGGER_REGION = os.getenv('AWS_BATCH_TRIGGER_REGION', os.getenv('AWS_S3_REGION_NAME', 'eu-west-1'))
AWS_BATCH_TRIGGER_ACCESS_KEY_ID = os.getenv('AWS_BATCH_TRIGGER_ACCESS_KEY_ID')
AWS_BATCH_TRIGGER_SECRET_ACCESS_KEY = os.getenv('AWS_BATCH_TRIGGER_SECRET_ACCESS_KEY')
AWS_BATCH_TRIGGER_SESSION_TOKEN = os.getenv('AWS_BATCH_TRIGGER_SESSION_TOKEN')

# --- Routing & Security ---
ALLOWED_HOSTS = [host.strip() for host in os.environ.get('ALLOWED_HOSTS', '').split(',') if host.strip()]
CSRF_TRUSTED_ORIGINS = [host.strip() for host in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if host.strip()]
LOCAL_KUBECTL_PROXY_URL = os.environ.get('LOCAL_KUBECTL_PROXY_URL')

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
    if origin.strip()
]
if not CORS_ALLOWED_ORIGINS and DEBUG:
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:5174',
        'http://127.0.0.1:5174',
    ]
CORS_ALLOW_CREDENTIALS = True

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ------------------------------------------- Static Files -------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',      
    'rest_framework.authtoken', 
    'django_filters',
    'drf_spectacular',      
    'jobs',
    'storages',
]

#------------------------ DRF & API Documentation Settings ------------------------
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Notebook Platform API',
    'DESCRIPTION': 'API for automating and managing Jupyter/R Notebook executions via Kubernetes.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SECURITY': [{'Token': []}], 
}
#------------------------------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'notebook_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'notebook_platform.wsgi.application'

# ------------------------------------------- Database Configuration -------------------------------------------
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

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

# ------------------------------------------- Storage Configuration -------------------------------------------
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'local').lower()

AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True

if AWS_S3_ENDPOINT_URL:
    AWS_S3_ADDRESSING_STYLE = "path"
    
    if ENVIRONMENT == "local":
        AWS_S3_CUSTOM_DOMAIN = f"localhost:9000/{AWS_STORAGE_BUCKET_NAME}"
        AWS_S3_URL_PROTOCOL = 'http:'
        AWS_QUERYSTRING_AUTH = False 

if AWS_STORAGE_BUCKET_NAME:
    default_storage_backend = 'storages.backends.s3boto3.S3Boto3Storage'
else:
    default_storage_backend = 'django.core.files.storage.FileSystemStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STORAGES = {
    "default": {
        "BACKEND": default_storage_backend,
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ----------------------------------- Celery Configuration -----------------------------------
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
