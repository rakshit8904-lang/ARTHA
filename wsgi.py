"""Entry point for gunicorn: gunicorn wsgi:app.

A local .env is loaded before the production default is applied. Deployments should
provide secrets through their environment/secret manager rather than uploading .env.
"""
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # pragma: no cover
    pass

import os
os.environ.setdefault("APP_ENV", "production")

from app import create_app  # noqa: E402
app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=app.config.get("APP_ENV") == "development")
