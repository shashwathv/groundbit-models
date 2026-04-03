# middleware/cors.py

import os
from fastapi.middleware.cors import CORSMiddleware


def add_cors(app):
    """
    Dashboard spec requirements:
    - Access-Control-Allow-Origin: *
    - OPTIONS preflight must return 204 with CORS headers
    - allow_credentials must be False when origins = ["*"]
    """
    ENV = os.getenv("ENV", "development")

    if ENV == "production":
        origins = [os.getenv("FRONTEND_URL", "https://yourfrontend.com")]
    else:
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,     # must be False when origins = ["*"]
        allow_methods=["*"],         # includes OPTIONS for preflight
        allow_headers=["*"],
        expose_headers=["*"]
    )