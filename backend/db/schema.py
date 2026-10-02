from typing import Dict, Any, List, Optional
from sqlalchemy import inspect, text
from backend.config import settings
from backend.db.connection import get_engine


def get_db_schema() -> Dict[str, Any]:
    """
    Introspects the current database schema.
    Returns tables, columns, data types, primary keys, foreign keys, and approximate row counts.
    """
    engine = get_engine()
    inspector = inspect(engine)
    schema_name = settings.db.schema_name if settings.db.mode == "postgres" else None

    table_names = inspector.get_table_names(schema=schema_name)
    tables_meta = []

    with engine.connect() as conn:
        for tname in table_names:
            columns = inspector.get_columns(tname, schema=schema_name)
            pk = inspector.get_pk_constraint(tname, schema=schema_name)
            pk_cols = set(pk.get("constrained_columns", [])) if pk else set()
            fks = inspector.get_foreign_keys(tname, schema=schema_name)

            # Get row count
            row_count = 0
            try:
                qualified_name = f'"{schema_name}"."{tname}"' if schema_name else f'"{tname}"'
                count_res = conn.execute(text(f"SELECT COUNT(*) FROM {qualified_name};")).scalar()
                row_count = count_res or 0
            except Exception:
                row_count = 0

            cols_meta = []
            for col in columns:
                col_name = col["name"]
                col_type = str(col["type"])
                is_pk = col_name in pk_cols
                
                # Check if foreign key
                fk_target = None
                for fk in fks:
                    if col_name in fk.get("constrained_columns", []):
                        idx = fk["constrained_columns"].index(col_name)
                        referred_table = fk.get("referred_table")
                        referred_cols = fk.get("referred_columns", [])
                        if idx < len(referred_cols):
                            fk_target = f"{referred_table}.{referred_cols[idx]}"
                        break

                cols_meta.append({
                    "name": col_name,
                    "type": col_type,
                    "nullable": col.get("nullable", True),
                    "is_primary_key": is_pk,
                    "foreign_key": fk_target,
                    "default": str(col.get("default", "")) if col.get("default") else None
                })

            tables_meta.append({
                "table_name": tname,
                "row_count": row_count,
                "columns": cols_meta,
                "primary_keys": list(pk_cols),
                "foreign_keys": [
                    {
                        "constrained_columns": fk.get("constrained_columns", []),
                        "referred_table": fk.get("referred_table"),
                        "referred_columns": fk.get("referred_columns", [])
                    }
                    for fk in fks
                ]
            })

    return {
        "database": settings.db.database if settings.db.mode == "postgres" else "Sample E-Commerce (SQLite)",
        "mode": settings.db.mode,
        "schema": schema_name or "public",
        "tables": tables_meta,
        "table_count": len(tables_meta)
    }


def format_schema_for_llm(schema_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Generates a concise markdown DDL representation of the database schema for the LLM.
    """
    if schema_data is None:
        schema_data = get_db_schema()

    lines = []
    lines.append(f"Database dialect: {'PostgreSQL' if settings.db.mode == 'postgres' else 'SQLite / Standard SQL'}")
    lines.append("Schema Tables:")

    for table in schema_data.get("tables", []):
        tname = table["table_name"]
        row_count = table.get("row_count", 0)
        lines.append(f"\nTable: {tname} (~{row_count} rows)")
        
        col_strs = []
        for col in table["columns"]:
            parts = [f"  - {col['name']} ({col['type']})"]
            if col["is_primary_key"]:
                parts.append("[PRIMARY KEY]")
            if col["foreign_key"]:
                parts.append(f"[REFERENCES {col['foreign_key']}]")
            col_strs.append(" ".join(parts))
        lines.extend(col_strs)

    return "\n".join(lines)


def get_table_preview(table_name: str, limit: int = 10) -> Dict[str, Any]:
    """Returns sample rows from a table."""
    engine = get_engine()
    schema_name = settings.db.schema_name if settings.db.mode == "postgres" else None
    qualified_name = f'"{schema_name}"."{table_name}"' if schema_name else f'"{table_name}"'

    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {qualified_name} LIMIT {limit};"))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]

    return {
        "table_name": table_name,
        "columns": columns,
        "rows": rows,
        "count": len(rows)
    }


def get_suggested_presets(schema_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    """Returns intelligent context-aware suggested natural language queries."""
    if schema_data is None:
        schema_data = get_db_schema()

    table_names = [t["table_name"].lower() for t in schema_data.get("tables", [])]

    if "orders" in table_names and "products" in table_names:
        return [
            {"title": "Top 5 Products", "query": "What are our top 5 best-selling products by total revenue?"},
            {"title": "Monthly Revenue", "query": "Show monthly sales revenue trend over time"},
            {"title": "High-Value Customers", "query": "List customers who have spent more than $500 in total"},
            {"title": "Category Performance", "query": "What is the average rating and total units sold for each product category?"},
            {"title": "Low Stock Alert", "query": "Show all products with stock quantity less than 50, sorted by lowest stock first"},
            {"title": "Order Status Distribution", "query": "Break down order counts and percentages by order status"},
        ]
    
    # Generic suggestions for any database
    presets = []
    for t in schema_data.get("tables", [])[:3]:
        presets.append({
            "title": f"Count {t['table_name']}",
            "query": f"How many total records are in the {t['table_name']} table?"
        })
        presets.append({
            "title": f"Recent {t['table_name']}",
            "query": f"Show the first 10 rows from {t['table_name']}"
        })
    return presets
