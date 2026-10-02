import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.db.sample_db import init_sample_database
from backend.db.connection import get_engine
from backend.routes.chat import router as chat_router
from backend.routes.db_routes import router as db_router
from backend.routes.config_routes import router as config_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure sample DB exists if starting in sample mode
    if settings.db.mode == "sample":
        init_sample_database()
    # Eagerly initialize engine
    try:
        get_engine()
    except Exception as e:
        print(f"[Warning] Initial DB connection check: {e}")
    yield
    # Shutdown logic if needed


app = FastAPI(
    title="PostgreSQL Natural Language Chat API",
    description="Interact with PostgreSQL databases in plain English using multi-provider LLMs.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(chat_router)
app.include_router(db_router)
app.include_router(config_router)

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
