import json
import re
from typing import Dict, Any, Optional, List
import sqlparse

from backend.config import settings
from backend.db.schema import get_db_schema, format_schema_for_llm
from backend.ai.provider import generate_completion, AIProviderError, mock_text_to_sql


def get_system_prompt(dialect: str, schema_text: str) -> str:
    return f"""You are an expert SQL engineer and data analyst specializing in {dialect}.
Your task is to convert the user's natural language question into an accurate, optimized, and secure SQL query based solely on the provided database schema.

### Database Schema:
{schema_text}

### Instructions & Rules:
1. Dialect: {dialect}. Strictly use valid syntax for {dialect}.
   - If PostgreSQL: Use proper double quotes for identifiers if needed, standard date functions (e.g. DATE_TRUNC, EXTRACT), ILIKE for case-insensitive matching.
   - If SQLite: Use strftime() for dates, LIKE for case-insensitivity.
2. Safety: Generate ONLY read-only queries (SELECT, WITH clauses). NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or CREATE statements.
3. Quality:
   - Provide clean, readable aliases for computed columns (e.g. total_revenue, order_count).
   - Use proper JOIN conditions referencing foreign keys.
   - Filter out cancelled or irrelevant records when appropriate.
   - When asked for "top" or "highest", order descending and apply an appropriate LIMIT (e.g. 5, 10) unless asked otherwise.
4. Output Format:
You MUST respond with a single, valid JSON object and NOTHING ELSE. No extra chatter outside the JSON.
Schema of the JSON object:
{{
  "sql": "SELECT ...;",
  "explanation": "Clear explanation of how the query answers the user question in 1-3 sentences.",
  "chart_recommendation": {{
    "chart_type": "bar" | "line" | "pie" | "doughnut" | "metric" | "table",
    "x_column": "Column name for X axis or categories",
    "y_column": "Column name for Y axis or numeric values",
    "title": "Title for the chart"
  }}
}}
- Use "bar" for comparing categories.
- Use "line" for dates/time-series trends.
- Use "pie" or "doughnut" for parts-of-a-whole distributions (<= 7 categories).
- Use "metric" if the result is a single aggregate number.
- Use "table" for multi-column record lists or when charting is not applicable.
"""


def clean_llm_json(response_text: str) -> Dict[str, Any]:
    """Cleans markdown fences or surrounding noise and parses JSON."""
    text = response_text.strip()
    
    # Strip markdown ```json ... ```
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Regex search for the first JSON block { ... }
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise AIProviderError(f"Could not parse valid JSON from AI response: {text[:200]}")


async def generate_sql_for_question(
    user_question: str,
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Translates natural language to SQL query with explanations and chart recommendations.
    """
    dialect = "PostgreSQL" if settings.db.mode == "postgres" else "SQLite / Standard SQL"
    schema_text = format_schema_for_llm()
    system_instruction = get_system_prompt(dialect, schema_text)

    # Build prompt with history if any
    prompt_parts = []
    if history:
        prompt_parts.append("Recent conversation history:")
        for msg in history[-4:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"{role.capitalize()}: {content}")
        prompt_parts.append("")

    prompt_parts.append(f"User Question: {user_question}")
    full_prompt = "\n".join(prompt_parts)

    try:
        raw_response = await generate_completion(
            prompt=full_prompt,
            system_instruction=system_instruction
        )
        data = clean_llm_json(raw_response)
    except Exception as e:
        # If AI call failed and no API key, fallback gracefully
        if not settings.ai.gemini_api_key and not settings.ai.openai_api_key:
            data = mock_text_to_sql(user_question)
        else:
            raise AIProviderError(str(e))

    # Format the SQL cleanly
    raw_sql = data.get("sql", "").strip()
    formatted_sql = sqlparse.format(
        raw_sql,
        reindent=True,
        keyword_case="upper",
        identifier_case="lower"
    ) if raw_sql else raw_sql

    data["sql"] = formatted_sql
    return data
