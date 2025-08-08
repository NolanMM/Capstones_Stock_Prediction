from .settings import *

# Use SQLite for testing to avoid MSSQL compatibility issues
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

DEBUG = True
ALLOWED_HOSTS = ['*']

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
