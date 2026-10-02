import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.ai.sql_generator import generate_sql_for_question
from backend.ai.sql_explainer import summarize_results
from backend.db.connection import execute_query
from backend.db.schema import get_suggested_presets, get_db_schema

router = APIRouter(prefix="/api", tags=["chat"])

# In-memory conversation store for chat history
conversations: Dict[str, List[Dict[str, str]]] = {}


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    execute: bool = True
    allow_modifications: bool = False


class ExecuteSQLRequest(BaseModel):
    sql: str
    allow_modifications: bool = False


def _auto_detect_chart(columns: List[str], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Smart chart type recommendation based on column data and row counts."""
    if not rows or len(columns) < 2:
        return {"chart_type": "table", "x_column": "", "y_column": "", "title": "Query Results"}

    col_types = {}
    first_row = rows[0]
    for col in columns:
        val = first_row.get(col)
        if isinstance(val, (int, float)):
            col_types[col] = "numeric"
        else:
            col_types[col] = "string"

    numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
    string_cols = [c for c, t in col_types.items() if t == "string"]

    if numeric_cols and string_cols:
        x_col = string_cols[0]
        y_col = numeric_cols[0]
        
        # Check if date/month
        if any(d in x_col.lower() for d in ["date", "month", "year", "day", "time"]):
            return {"chart_type": "line", "x_column": x_col, "y_column": y_col, "title": f"{y_col} Over Time"}
        
        if len(rows) <= 6:
            return {"chart_type": "doughnut", "x_column": x_col, "y_column": y_col, "title": f"{y_col} by {x_col}"}
        
        return {"chart_type": "bar", "x_column": x_col, "y_column": y_col, "title": f"{y_col} by {x_col}"}

    return {"chart_type": "table", "x_column": "", "y_column": "", "title": "Query Results"}


@router.post("/chat")
async def chat(request: ChatRequest):
    cid = request.conversation_id or str(uuid.uuid4())
    history = conversations.setdefault(cid, [])

    # Step 1: Generate SQL from natural language
    try:
        gen_result = await generate_sql_for_question(
            user_question=request.message,
            history=history
        )
    except Exception as e:
        return {
            "success": False,
            "conversation_id": cid,
            "question": request.message,
            "sql": "",
            "explanation": "",
            "error": f"Failed to generate SQL: {str(e)}",
            "results": None,
            "summary_insight": ""
        }

    sql = gen_result.get("sql", "")
    explanation = gen_result.get("explanation", "")
    chart_rec = gen_result.get("chart_recommendation", {})

    # Append to conversation history
    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": f"SQL: {sql}\nExplanation: {explanation}"})

    # Step 2: Execute query if requested
    query_results = None
    summary_insight = ""

    if request.execute and sql:
        query_results = execute_query(sql, allow_modifications=request.allow_modifications)
        
        if query_results.get("success") and query_results.get("rows"):
            columns = query_results.get("columns", [])
            rows = query_results.get("rows", [])
            
            # Refine chart recommendation if needed
            if not chart_rec or chart_rec.get("chart_type") == "table":
                chart_rec = _auto_detect_chart(columns, rows)
                
            # Generate analytical summary
            summary_insight = await summarize_results(
                user_question=request.message,
                sql=sql,
                columns=columns,
                rows=rows
            )

    return {
        "success": True,
        "conversation_id": cid,
        "question": request.message,
        "sql": sql,
        "explanation": explanation,
        "chart_recommendation": chart_rec,
        "results": query_results,
        "summary_insight": summary_insight,
        "error": query_results.get("error") if (query_results and not query_results.get("success")) else None
    }


@router.post("/query/execute")
async def run_raw_sql(request: ExecuteSQLRequest):
    """Executes a custom or user-edited SQL query directly."""
    result = execute_query(request.sql, allow_modifications=request.allow_modifications)
    chart_rec = {"chart_type": "table", "x_column": "", "y_column": "", "title": "Query Results"}
    
    if result.get("success") and result.get("rows"):
        chart_rec = _auto_detect_chart(result.get("columns", []), result.get("rows", []))

    return {
        "success": result.get("success", False),
        "results": result,
        "chart_recommendation": chart_rec,
        "sql": request.sql,
        "error": result.get("error")
    }


@router.get("/presets")
async def get_presets():
    """Returns contextual preset question suggestions based on active schema."""
    try:
        presets = get_suggested_presets()
        return {"presets": presets}
    except Exception as e:
        return {"presets": [], "error": str(e)}
