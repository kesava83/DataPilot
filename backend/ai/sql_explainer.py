import json
from typing import Dict, Any, List
from backend.config import settings
from backend.ai.provider import generate_completion


async def summarize_results(user_question: str, sql: str, columns: List[str], rows: List[Dict[str, Any]]) -> str:
    """
    Summarizes query execution results into 1-2 insightful natural language sentences.
    """
    if not rows:
        return "The query executed successfully but returned 0 records matching the criteria."

    # If only 1 or 2 rows
    if len(rows) == 1:
        item = rows[0]
        summary_items = [f"{k}: **{v}**" for k, v in list(item.items())[:3]]
        return f"Found 1 result: {', '.join(summary_items)}."

    # Heuristic quick summary if no API key is present
    has_api_key = bool(settings.ai.gemini_api_key or settings.ai.openai_api_key or settings.ai.provider == "ollama")
    if not has_api_key:
        first_row = rows[0]
        # Look for numeric or key column
        first_keys = list(first_row.keys())
        name_val = first_row.get(first_keys[0])
        val_val = first_row.get(first_keys[-1])
        return f"Returned **{len(rows)}** records. The top entry is **{name_val}** with **{val_val}**."

    # Use LLM for intelligent business insight
    sample_data = rows[:8]
    prompt = f"""Question: {user_question}
Executed SQL: {sql}
Returned Results ({len(rows)} rows, showing sample of first {len(sample_data)}):
{json.dumps(sample_data, default=str)}

Write a concise 1-2 sentence business insight summarizing the key takeaways from these results. Highlight key figures or standout patterns. Do not repeat raw SQL."""

    try:
        summary = await generate_completion(
            prompt=prompt,
            system_instruction="You are a data analyst. Provide a brief, high-impact 1-2 sentence executive summary of query results."
        )
        return summary.strip().strip('"')
    except Exception:
        return f"Successfully retrieved **{len(rows)}** records answering your question."
