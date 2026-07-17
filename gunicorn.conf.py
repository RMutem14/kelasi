"""
Configuration Gunicorn pour Huduma.

Usage :
    gunicorn config.wsgi:application -c gunicorn.conf.py

Variables d'environnement :
    GUNICORN_BIND          — adresse d'écoute (défaut : 0.0.0.0:8000)
    GUNICORN_WORKERS       — nombre de workers
    GUNICORN_TIMEOUT       — timeout en secondes
    GUNICORN_MAX_REQUESTS  — max requêtes par worker avant restart
    GUNICORN_LOG_LEVEL     — niveau de log
"""
import multiprocessing
import os

def _env(key, default):
    return os.environ.get(key, default)

bind = _env("GUNICORN_BIND", "0.0.0.0:8000")
workers = int(_env("GUNICORN_WORKERS", str(min(4, multiprocessing.cpu_count() * 2 + 1))))
worker_class = "sync"
timeout = int(_env("GUNICORN_TIMEOUT", "60"))
keepalive = 5
max_requests = int(_env("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = 50
graceful_timeout = 30

loglevel = _env("GUNICORN_LOG_LEVEL", "info")
accesslog = _env("GUNICORN_ACCESS_LOG", "-")
errorlog = _env("GUNICORN_ERROR_LOG", "-")

# Sécurité
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Optimisations
preload_app = True
