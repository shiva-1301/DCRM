"""
Production entrypoint: `gunicorn wsgi:app`
"""
from backend.app import create_app, _bootstrap_ml
from backend.database.database import ensure_indexes, initialize_default_admin

app = create_app()

with app.app_context():
    ensure_indexes()
    initialize_default_admin()

_bootstrap_ml(app)
