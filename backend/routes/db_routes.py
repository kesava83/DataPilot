from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.config import settings, DBConfig
from backend.db.connection import test_connection, reset_engine, get_engine
from backend.db.schema import get_db_schema, get_table_preview

router = APIRouter(prefix="/api/db", tags=["database"])


class ConnectRequest(BaseModel):
    mode: str = "postgres"  # 'postgres' or 'sample'
    host: Optional[str] = "localhost"
    port: Optional[int] = 5432
    database: Optional[str] = "postgres"
    user: Optional[str] = "postgres"
    password: Optional[str] = ""
    sslmode: Optional[str] = "prefer"
    schema_name: Optional[str] = "public"


@router.get("/status")
def get_db_status():
    """Returns the current database connection status."""
    try:
        schema = get_db_schema()
        return {
            "connected": True,
            "mode": settings.db.mode,
            "database": settings.db.database if settings.db.mode == "postgres" else "sample_ecommerce.db",
            "host": settings.db.host if settings.db.mode == "postgres" else "Local (SQLite)",
            "port": settings.db.port if settings.db.mode == "postgres" else None,
            "user": settings.db.user if settings.db.mode == "postgres" else "local",
            "schema": settings.db.schema_name if settings.db.mode == "postgres" else "main",
            "table_count": schema.get("table_count", 0),
            "tables": [t["table_name"] for t in schema.get("tables", [])]
        }
    except Exception as e:
        return {
            "connected": False,
            "mode": settings.db.mode,
            "error": str(e),
            "table_count": 0,
            "tables": []
        }


@router.post("/test")
def test_db_credentials(req: ConnectRequest):
    """Tests a database connection configuration without applying it."""
    cfg = DBConfig(
        mode=req.mode,  # type: ignore
        host=req.host or "localhost",
        port=req.port or 5432,
        database=req.database or "postgres",
        user=req.user or "postgres",
        password=req.password or "",
        sslmode=req.sslmode or "prefer",
        schema_name=req.schema_name or "public",
    )
    result = test_connection(cfg)
    return result


@router.post("/connect")
def connect_database(req: ConnectRequest):
    """
    Updates the active database configuration and reconnects.
    Can switch to PostgreSQL with user credentials or switch back to Sample Mode.
    """
    new_cfg = DBConfig(
        mode=req.mode,  # type: ignore
        host=req.host or "localhost",
        port=req.port or 5432,
        database=req.database or "postgres",
        user=req.user or "postgres",
        password=req.password or "",
        sslmode=req.sslmode or "prefer",
        schema_name=req.schema_name or "public",
    )

    # Test before making active
    test_res = test_connection(new_cfg)
    if not test_res.get("success"):
        raise HTTPException(status_code=400, detail=f"Connection test failed: {test_res.get('error')}")

    # Apply configuration and reset engine
    reset_engine()
    settings.db = new_cfg
    # Re-instantiate engine to verify
    get_engine(force_reconnect=True)

    # Fetch fresh schema
    schema = get_db_schema()

    return {
        "success": True,
        "message": f"Successfully connected to {new_cfg.database} ({new_cfg.mode.upper()})",
        "mode": new_cfg.mode,
        "table_count": schema.get("table_count", 0),
        "tables": schema.get("tables", [])
    }


@router.get("/schema")
def get_schema():
    """Returns detailed schema information for the active database."""
    try:
        return get_db_schema()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch schema: {str(e)}")


@router.get("/preview/{table_name}")
def preview_table(table_name: str, limit: int = 10):
    """Returns sample rows from the given table."""
    try:
        return get_table_preview(table_name, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview table {table_name}: {str(e)}")
