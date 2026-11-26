from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env(
    TEST_DB_NAME=(str, "shopsphere_test"),
    TEST_DB_USER=(str, "shopsphere_app"),
    TEST_DB_PASSWORD=(str, ""),
    TEST_DB_HOST=(str, "127.0.0.1"),
    TEST_DB_PORT=(str, "5432"),
)

env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = "test-insecure-secret-key-for-local-pytest-only"
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "apps.common",
    "apps.geo",
    "apps.messaging",
    "apps.audit",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("TEST_DB_NAME"),
        "USER": env("TEST_DB_USER"),
        "PASSWORD": env("TEST_DB_PASSWORD"),
        "HOST": env("TEST_DB_HOST"),
        "PORT": env("TEST_DB_PORT"),
        "TEST": {
            "NAME": env("TEST_DB_NAME"),
        },
    }
}

USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
