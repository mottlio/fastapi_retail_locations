# app/main.py
from fastapi import FastAPI, Query
from .db import find_nearby, Session, text

app = FastAPI(title="Acme Payments API",
    description="""Simple REST API for payments.

**Notes**
- Auth via Bearer token
- Rate limit: 60 req/min
""",
    version="0.1.0",
    license_info={"name": "Apache 2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"},
    docs_url="/docs",          # Swagger UI location (default: /docs)
    redoc_url="/redoc",        # ReDoc location (default: /redoc)
    openapi_url="/openapi.json",
    # Optional Swagger UI tweaks:
    swagger_ui_parameters={
        "docExpansion": "none",
        "displayRequestDuration": True,
        "persistAuthorization": True,
        "filter": True,               # search box
        "tryItOutEnabled": True,
        "defaultModelsExpandDepth": -1
    },
    # If supported in your FastAPI version:
    # swagger_ui_favicon_url="https://your.cdn/favicon.ico",
    )

@app.get("/api/nearby")
async def nearby(lat: float = Query(...), lon: float = Query(...), km: float = 10, limit: int = 50):
    limit = min(max(limit, 1), 100)  # clamp
    return await find_nearby(lat, lon, km, limit)

@app.get("/health")
async def health():
    # Light DB ping (optional)
    try:
        async with Session() as s:
            await s.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "db_error", "detail": str(e)}