import time
import re
import decimal
import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
import sqlparse

from backend.config import settings, DBConfig
from backend.db.sample_db import init_sample_database

# Cached active engine
_engine: Optional[Engine] = None
_current_connection_str: Optional[str] = None


def get_engine(config: Optional[DBConfig] = None, force_reconnect: bool = False) -> Engine:
    global _engine, _current_connection_str
    target_config = config or settings.db

    conn_url = target_config.connection_url
    if _engine is not None and not force_reconnect and _current_connection_str == conn_url:
        return _engine

    if target_config.mode == "sample":
        init_sample_database()
        _engine = create_engine(conn_url, connect_args={"check_same_thread": False})
    else:
        # PostgreSQL with psycopg3
        _engine = create_engine(
            conn_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=10,
        )

    _current_connection_str = conn_url
    return _engine


def reset_engine():
    global _engine, _current_connection_str
    if _engine is not None:
        try:
            _engine.dispose()
        except Exception:
            pass
    _engine = None
    _current_connection_str = None


def test_connection(config: DBConfig) -> Dict[str, Any]:
    """
    Tests connectivity to the specified database configuration without making it active.
    Returns status, latency in ms, database version, and detected tables.
    """
    start_time = time.time()
    try:
        if config.mode == "sample":
            init_sample_database()
            test_engine = create_engine("sqlite:///./sample_ecommerce.db")
            with test_engine.connect() as conn:
                res = conn.execute(text("SELECT sqlite_version();")).scalar()
            inspector = inspect(test_engine)
            tables = inspector.get_table_names()
            test_engine.dispose()
            return {
                "success": True,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "version": f"SQLite {res} (Sample Demo DB)",
                "tables": tables,
                "table_count": len(tables),
                "message": "Sample Database connection successful!",
            }
        else:
            test_engine = create_engine(config.connection_url, connect_args={"connect_timeout": 5})
            with test_engine.connect() as conn:
                res = conn.execute(text("SELECT version();")).scalar()
            inspector = inspect(test_engine)
            tables = inspector.get_table_names(schema=config.schema_name or "public")
            test_engine.dispose()
            return {
                "success": True,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "version": str(res).split("\n")[0] if res else "PostgreSQL",
                "tables": tables,
                "table_count": len(tables),
                "message": "PostgreSQL connection established successfully!",
            }
    except Exception as e:
        return {
            "success": False,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
            "error": str(e),
            "message": f"Connection failed: {str(e)}",
        }


def validate_sql_safety(sql: str, allow_modifications: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Checks if the SQL query contains prohibited mutation statements when read-only mode is active.
    """
    # Clean and split into individual statements
    parsed = sqlparse.parse(sql)
    if not parsed:
        return False, "Query is empty."

    # Forbidden keywords in read-only mode
    destructive_keywords = [
        "DROP", "TRUNCATE", "DELETE", "UPDATE", "INSERT",
        "ALTER", "CREATE", "REPLACE", "GRANT", "REVOKE"
    ]

    for stmt in parsed:
        stmt_text = str(stmt).strip()
        first_token = stmt.get_type().upper() if stmt.get_type() else ""
        
        # Check tokens
        for token in stmt.flatten():
            val = token.value.upper()
            if not allow_modifications and val in destructive_keywords:
                return False, f"Safety restriction: Query contains '{val}' operation. Read-only mode is enabled."

    return True, None


def _serialize_value(val: Any) -> Any:
    """Helper to serialize dates, decimals, bytes to JSON-friendly formats."""
    if isinstance(val, (datetime.date, datetime.datetime, datetime.time)):
        return val.isoformat()
    if isinstance(val, decimal.Decimal):
        return float(val)
    if isinstance(val, bytes):
        return f"<bytes: {len(val)} bytes>"
    return val


def execute_query(sql: str, max_rows: int = 500, allow_modifications: bool = False) -> Dict[str, Any]:
    """
    Executes a SQL query against the currently active database engine.
    Returns columns, rows, execution time, and total row count.
    """
    is_safe, error_msg = validate_sql_safety(sql, allow_modifications=allow_modifications)
    if not is_safe:
        return {
            "success": False,
            "error": error_msg,
            "sql": sql,
            "execution_time_ms": 0,
        }

    engine = get_engine()
    start_time = time.time()

    try:
        with engine.connect() as conn:
            # Set statement timeout for postgres if supported
            if settings.db.mode == "postgres":
                try:
                    conn.execute(text("SET statement_timeout = '15s';"))
                except Exception:
                    pass

            result = conn.execute(text(sql))
            execution_time_ms = round((time.time() - start_time) * 1000, 2)

            if result.returns_rows:
                columns = list(result.keys())
                raw_rows = result.fetchmany(max_rows)
                rows = [
                    {col: _serialize_value(row[idx]) for idx, col in enumerate(columns)}
                    for row in raw_rows
                ]
                has_more = len(raw_rows) == max_rows
                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "has_more": has_more,
                    "execution_time_ms": execution_time_ms,
                    "sql": sql,
                }
            else:
                conn.commit()
                return {
                    "success": True,
                    "columns": [],
                    "rows": [],
                    "row_count": result.rowcount,
                    "execution_time_ms": execution_time_ms,
                    "message": f"Query executed successfully ({result.rowcount} rows affected).",
                    "sql": sql,
                }

    except Exception as e:
        execution_time_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "success": False,
            "error": str(e),
            "execution_time_ms": execution_time_ms,
            "sql": sql,
        }
