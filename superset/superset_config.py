import os

from neoretail_publication import register_neoretail_publication

SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "change-me-local-only")
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SUPERSET_METADATA_URI",
    "postgresql+psycopg2://superset:superset@superset-db:5432/superset",
)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "neoretail_superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": 1,
}
DATA_CACHE_CONFIG = {
    **CACHE_CONFIG,
    "CACHE_KEY_PREFIX": "neoretail_data_",
    "CACHE_REDIS_DB": 2,
}
FILTER_STATE_CACHE_CONFIG = {
    **CACHE_CONFIG,
    "CACHE_KEY_PREFIX": "neoretail_filters_",
    "CACHE_REDIS_DB": 3,
}
EXPLORE_FORM_DATA_CACHE_CONFIG = {
    **CACHE_CONFIG,
    "CACHE_KEY_PREFIX": "neoretail_explore_",
    "CACHE_REDIS_DB": 4,
}

FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "CHART_PLUGINS_EXPERIMENTAL": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "EMBEDDED_SUPERSET": True,
    "DISABLE_EMBEDDED_SUPERSET_LOGOUT": True,
}

GUEST_TOKEN_JWT_SECRET = os.getenv("GUEST_TOKEN_JWT_SECRET", SECRET_KEY)
GUEST_TOKEN_JWT_AUDIENCE = "superset"
GUEST_TOKEN_JWT_EXP_SECONDS = 300
GUEST_ROLE_NAME = "Gamma"

ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "origins": ["http://localhost:3000"],
}

# POC local HTTP. Em produção, HTTPS + cookie Secure + Allowed Domains restritos.
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
TALISMAN_ENABLED = True
TALISMAN_CONFIG = {
    "content_security_policy": {
        "default-src": ["'self'"],
        "img-src": ["'self'", "data:", "blob:"],
        "worker-src": ["'self'", "blob:"],
        "connect-src": ["'self'", "http://localhost:3000"],
        "frame-ancestors": ["'self'", "http://localhost:3000"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "script-src": ["'self'", "'unsafe-eval'", "'unsafe-inline'"],
    },
    "force_https": False,
}

ENABLE_PROXY_FIX = True
FLASK_APP_MUTATOR = register_neoretail_publication
ROW_LIMIT = 100000
SQL_MAX_ROW = 100000
SQLLAB_TIMEOUT = 180
SUPERSET_WEBSERVER_TIMEOUT = 180
WTF_CSRF_ENABLED = True

# O visual Handlebars continua sanitizado. Liberamos apenas as tags e os
# atributos necessarios para CSS local e para o pequeno grafico SVG dos cards.
HTML_SANITIZATION = True
HTML_SANITIZATION_SCHEMA_EXTENSIONS = {
    "tagNames": ["style", "header", "svg", "polygon", "polyline"],
    "attributes": {
        "div": ["className"],
        "header": ["className"],
        "span": ["className"],
        "a": ["className"],
        "svg": ["className", "viewBox", "preserveAspectRatio", "role", "aria-label"],
        "polygon": ["points", "fill", "fill-opacity"],
        "polyline": [
            "points",
            "fill",
            "stroke",
            "stroke-width",
            "stroke-linecap",
            "stroke-linejoin",
        ],
    },
}

# O Superset consulta somente gold.*. PostgreSQL acima é metadata interna.
DEFAULT_DB_ID = None
