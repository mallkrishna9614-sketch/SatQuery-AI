from fastapi import FastAPI
from app.api.routes_compatibility import router as compatibility_router
from app.core.database import init_database
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_investigation import router as investigation_router
from app.api.routes_images import router as images_router
from app.core.config import settings
from app.core.errors import SatQueryError, satquery_error_handler


app = FastAPI(
    
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)
init_database()


# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Error Handler
# -----------------------------
app.add_exception_handler(
    SatQueryError,
    satquery_error_handler
)


# -----------------------------
# API Routes
# -----------------------------
app.include_router(
    images_router,
    prefix=settings.API_PREFIX
)
app.include_router(
    compatibility_router,
    prefix=settings.API_PREFIX
)
app.include_router(
    investigation_router,
    prefix=settings.API_PREFIX
)

# -----------------------------
# Health Check
# -----------------------------
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "satquery-backend"
    }