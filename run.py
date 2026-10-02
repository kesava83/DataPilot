import sys
import os
import uvicorn
from backend.config import settings
from backend.db.sample_db import init_sample_database

if __name__ == "__main__":
    print("=" * 60)
    print("  NLP AI - Natural Language PostgreSQL Studio")
    print("=" * 60)
    print(f"  * Mode:        {settings.db.mode.upper()}")
    print(f"  * AI Provider: {settings.ai.provider.upper()}")
    print(f"  * Server URL:  http://{settings.host}:{settings.port}")
    print("=" * 60)
    print("  Open http://localhost:8000 in your browser to start querying!")
    print("=" * 60 + "\n")

    # Initialize sample database for immediate zero-config testing
    init_sample_database()

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.host == "127.0.0.1",
        log_level="info"
    )
