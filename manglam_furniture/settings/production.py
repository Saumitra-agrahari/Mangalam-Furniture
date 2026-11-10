import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .base import *


def _env_bool(name, default):
    if not config(name, default="").strip():
        return default
    return config(name, cast=bool)


def _env_int(name, default):
    if not config(name, default="").strip():
        return default
    return config(name, cast=int)


def _require_env(name):
    value = config(name, default="").strip()
    if not value:
        raise ImproperlyConfigured(f"Missing required environment variable: {name}")
    return value


DEBUG = _env_bool("DEBUG", False)
SECRET_KEY = _require_env("SECRET_KEY")

ALLOWED_HOSTS = [
    host.strip()
    for host in config("ALLOWED_HOSTS", default="").split(",")
    if host.strip()
]
vercel_url = config("VERCEL_URL", default="").strip()
if vercel_url and vercel_url not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(vercel_url)
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("Missing required environment variable: ALLOWED_HOSTS")

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in config("CSRF_TRUSTED_ORIGINS", default="").split(",")
    if origin.strip()
]
if vercel_url:
    vercel_origin = f"https://{vercel_url}"
    if vercel_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(vercel_origin)

DATABASE_URL = _require_env("DATABASE_URL")
DATABASES["default"] = dj_database_url.parse(DATABASE_URL, conn_max_age=0)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = _env_bool("CSRF_COOKIE_SECURE", True)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="").strip()
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="").strip()
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="").strip()
_missing_s3 = [
    name
    for name, value in (
        ("AWS_ACCESS_KEY_ID", AWS_ACCESS_KEY_ID),
        ("AWS_SECRET_ACCESS_KEY", AWS_SECRET_ACCESS_KEY),
        ("AWS_STORAGE_BUCKET_NAME", AWS_STORAGE_BUCKET_NAME),
    )
    if not value
]
if _missing_s3:
    raise ImproperlyConfigured(
        f"Missing required S3 media storage environment variable(s): {', '.join(_missing_s3)}"
    )

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="").strip() or None
AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="").strip() or None
AWS_S3_CUSTOM_DOMAIN = config("AWS_S3_CUSTOM_DOMAIN", default="").strip() or None
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="").strip()
EMAIL_PORT = _env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="").strip()
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="").strip()
EMAIL_USE_TLS = _env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="").strip()
