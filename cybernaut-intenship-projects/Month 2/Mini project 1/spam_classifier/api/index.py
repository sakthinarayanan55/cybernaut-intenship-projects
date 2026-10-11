import os
import sys
from urllib.parse import parse_qs

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app


class VercelPathMiddleware:
    """Normalizes PATH_INFO when Vercel serverless rewrites route traffic
    via __path query parameter or serverless prefix."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. If Vercel passed original path via __path query param
        qs = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
        if "__path" in qs:
            val = qs["__path"][0] if qs["__path"] else ""
            if val:
                environ["PATH_INFO"] = "/" + val.lstrip("/")
            else:
                environ["PATH_INFO"] = "/"

        # 2. If PATH_INFO has /api/index[.py] prefix
        path = environ.get("PATH_INFO", "")
        for prefix in ("/api/index.py", "/api/index"):
            if path == prefix or path == prefix + "/":
                environ["PATH_INFO"] = "/"
                break
            elif path.startswith(prefix + "/"):
                remainder = path[len(prefix):]
                environ["PATH_INFO"] = remainder if remainder.startswith("/") else "/" + remainder
                break

        return self.wsgi_app(environ, start_response)


# Wrap Flask's WSGI application
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
