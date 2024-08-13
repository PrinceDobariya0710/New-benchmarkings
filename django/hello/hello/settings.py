import os

DEBUG = False

SECRET_KEY = '_7mb6#v4yf@qhc(r(zbyh&amp;z_iby-na*7wz&amp;-v6pohsul-d#y5f'
ADMINS = ()

MANAGERS = ADMINS

_django_db = os.getenv('DJANGO_DB', "postgresql")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.' + _django_db, # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.getenv("PGDB", "benchmark_db"),           # Or path to database file if using sqlite3.
        'USER': os.getenv("PGUSER", "postgres"),       # Not used with sqlite3.
        'PASSWORD': os.getenv("PGPASS", "root"),   # Not used with sqlite3.
        'HOST': os.getenv("PGHOST", "localhost"),          # Set to empty string for localhost. Not used with sqlite3.
        'PORT': 5432,                      # Set to empty string for default. Not used with sqlite3.
        'CONN_MAX_AGE': 30,
    }
}

if not _django_db:
    DATABASES = { }

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
USE_I18N = False
USE_L10N = False
USE_TZ = False

MEDIA_ROOT = ''
MEDIA_URL = ''
STATIC_ROOT = ''
STATIC_URL = '/static/'
STATICFILES_DIRS = ()
STATICFILES_FINDERS = ()
MIDDLEWARE = ()

ROOT_URLCONF = 'hello.urls'
WSGI_APPLICATION = 'hello.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {},
    },
]

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'world',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {},
    'loggers': {},

}

ALLOWED_HOSTS = ['*']
