"""
Production WSGI Entry Point for SafeRoute Application.
Compatible with Gunicorn, Waitress, uWSGI, or AWS Lambda / App Runner.

Usage:
  gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app
"""
import os
from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
