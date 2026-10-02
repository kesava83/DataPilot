import re
import json
import httpx
from typing import Dict, Any, Optional
from backend.config import settings


class AIProviderError(Exception):
    pass


async def call_gemini(prompt: str, system_instruction: str, api_key: str, model: str = "gemini-2.5-flash") -> str:
    """Calls Google Gemini REST API using httpx."""
    if not api_key:
        raise AIProviderError("Gemini API key is required. Please set it in Settings or .env file.")

    # Modern Gemini v1beta endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        }
    }

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                error_data = response.json().get("error", {})
                error_msg = error_data.get("message", response.text)
                raise AIProviderError(f"Gemini API Error ({response.status_code}): {error_msg}")

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise AIProviderError("Gemini returned no candidates.")
            
            content_parts = candidates[0].get("content", {}).get("parts", [])
            if not content_parts:
                raise AIProviderError("Gemini candidate has empty content.")
            
            return content_parts[0].get("text", "")
        except httpx.RequestError as e:
            raise AIProviderError(f"Network error communicating with Gemini API: {str(e)}")


async def call_openai(prompt: str, system_instruction: str, api_key: str, model: str = "gpt-4o-mini") -> str:
    """Calls OpenAI chat completion REST API using httpx."""
    if not api_key:
        raise AIProviderError("OpenAI API key is required. Please set it in Settings or .env file.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                error_data = response.json().get("error", {})
                error_msg = error_data.get("message", response.text)
                raise AIProviderError(f"OpenAI API Error ({response.status_code}): {error_msg}")

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise AIProviderError("OpenAI returned no choices.")
            return choices[0].get("message", {}).get("content", "")
        except httpx.RequestError as e:
            raise AIProviderError(f"Network error communicating with OpenAI API: {str(e)}")


async def call_ollama(prompt: str, system_instruction: str, base_url: str = "http://localhost:11434", model: str = "llama3:latest") -> str:
    """Calls local Ollama instance via HTTP API."""
    url = f"{base_url.rstrip('/')}/api/chat"
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raise AIProviderError(f"Ollama API Error ({response.status_code}): {response.text}")
            data = response.json()
            return data.get("message", {}).get("content", "")
        except httpx.ConnectError:
            raise AIProviderError(f"Cannot connect to Ollama at {base_url}. Please ensure Ollama is running.")
        except httpx.RequestError as e:
            raise AIProviderError(f"Network error communicating with Ollama: {str(e)}")


def mock_text_to_sql(user_question: str) -> Dict[str, Any]:
    """
    Intelligent fallback pattern matching when no API key is provided,
    allowing testing of the app immediately. Supports both sample eCommerce and custom PostgreSQL schemas.
    """
    if "User Question:" in user_question:
        user_question = user_question.split("User Question:")[-1].strip()

    q = user_question.lower()

    # Introspect active database tables
    tables = []
    tables_meta = {}
    try:
        from backend.db.schema import get_db_schema
        schema = get_db_schema()
        tables = [t["table_name"] for t in schema.get("tables", [])]
        tables_meta = {t["table_name"]: t for t in schema.get("tables", [])}
    except Exception:
        pass

    # Check if a custom table from the active schema is requested
    matched_table = None
    for t in tables:
        if t.lower() in q:
            matched_table = t
            break

    # If no schema table matched, check if user explicitly named a table (e.g. 'netflix_shows table' or 'for netflix_shows')
    if not matched_table:
        table_match = re.search(r'(?:for\s+the\s+|table\s+|from\s+|in\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s+table', q) or \
                      re.search(r'(?:for\s+the\s+|from\s+|in\s+table\s+)([a-zA-Z_][a-zA-Z0-9_]*)', q)
        if table_match:
            potential_name = table_match.group(1).strip()
            if potential_name not in ["the", "a", "an", "all", "each", "this", "that"]:
                matched_table = potential_name

    # If connected to a custom DB (e.g. postgres) where 'orders' doesn't exist, default to the first table
    if not matched_table and "orders" not in [t.lower() for t in tables] and tables:
        matched_table = tables[0]

    if matched_table:
        table_meta = tables_meta.get(matched_table, {})
        cols = [c["name"] for c in table_meta.get("columns", [])]
        quote = '"' if settings.db.mode == "postgres" else ''
        schema_prefix = f'{quote}{matched_table}{quote}'

        # Check if user asked for count/aggregate
        if any(w in q for w in ["count", "total records", "how many", "number of rows"]):
            return {
                "sql": f"SELECT COUNT(*) AS total_records FROM {schema_prefix};",
                "explanation": f"Counts the total records in table '{matched_table}'. (⚠️ Running in Demo/Fallback Mode: Add your Gemini API Key in Settings for custom generative AI queries).",
                "chart_recommendation": {
                    "chart_type": "metric",
                    "x_column": "",
                    "y_column": "total_records",
                    "title": f"Total Records in {matched_table}"
                }
            }

        # Check for category / type breakdown if relevant column exists or standard columns
        breakdown_col = next((c for c in cols if c.lower() in ["type", "category", "genre", "status", "country", "rating", "customer_tier"]), None)
        if not breakdown_col and "netflix" in matched_table.lower():
            breakdown_col = "type"

        if breakdown_col and any(w in q for w in ["summary", "analytics", "breakdown", "by type", "by category", "distribution"]):
            return {
                "sql": f"SELECT {quote}{breakdown_col}{quote}, COUNT(*) AS total_count FROM {schema_prefix} GROUP BY {quote}{breakdown_col}{quote} ORDER BY total_count DESC LIMIT 10;",
                "explanation": f"Groups and summarizes records in '{matched_table}' by '{breakdown_col}'. (⚠️ Running in Demo/Fallback Mode: Add your Gemini API Key in Settings for custom generative AI queries).",
                "chart_recommendation": {
                    "chart_type": "bar",
                    "x_column": breakdown_col,
                    "y_column": "total_count",
                    "title": f"Distribution by {breakdown_col}"
                }
            }

        # Default query for this table
        return {
            "sql": f"SELECT * FROM {schema_prefix} LIMIT 10;",
            "explanation": f"Retrieves recent sample records from table '{matched_table}'. (⚠️ Running in Demo/Fallback Mode: Add your Gemini API Key in Settings for custom generative AI queries).",
            "chart_recommendation": {
                "chart_type": "table",
                "x_column": "",
                "y_column": "",
                "title": f"Recent Records from {matched_table}"
            }
        }

    # Fallback to built-in eCommerce sample database pattern matches (only if orders/products exist in the DB or tables list is empty)
    has_ecommerce = not tables or any(t.lower() in ["orders", "products", "customers"] for t in tables)

    if has_ecommerce:
        if any(w in q for w in ["top product", "best selling", "top 5 product", "revenue by product"]):
            return {
                "sql": """SELECT p.name AS product_name,
       p.category,
       SUM(oi.quantity) AS total_units_sold,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS total_revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status != 'Cancelled'
GROUP BY p.product_id, p.name, p.category
ORDER BY total_revenue DESC
LIMIT 5;""",
                "explanation": "Calculates the top 5 revenue-generating products by joining products with order items, filtering out cancelled orders, and ordering by total revenue.",
                "chart_recommendation": {
                    "chart_type": "bar",
                    "x_column": "product_name",
                    "y_column": "total_revenue",
                    "title": "Top 5 Products by Revenue"
                }
            }
        elif any(w in q for w in ["monthly", "month", "trend", "sales over time"]):
            return {
                "sql": """SELECT strftime('%Y-%m', order_date) AS month,
       COUNT(DISTINCT order_id) AS total_orders,
       ROUND(SUM(total_amount), 2) AS total_sales
FROM orders
WHERE status != 'Cancelled'
GROUP BY strftime('%Y-%m', order_date)
ORDER BY month ASC;""",
                "explanation": "Aggregates completed and processing order revenue and order count by month to visualize revenue trends.",
                "chart_recommendation": {
                    "chart_type": "line",
                    "x_column": "month",
                    "y_column": "total_sales",
                    "title": "Monthly Revenue Trend"
                }
            }
        elif any(w in q for w in ["category", "categories", "department"]):
            return {
                "sql": """SELECT p.category,
       COUNT(DISTINCT p.product_id) AS product_count,
       ROUND(AVG(p.rating), 2) AS avg_rating,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS category_revenue
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY category_revenue DESC;""",
                "explanation": "Summarizes total revenue, product count, and average customer ratings across all product categories.",
                "chart_recommendation": {
                    "chart_type": "doughnut",
                    "x_column": "category",
                    "y_column": "category_revenue",
                    "title": "Revenue Distribution by Category"
                }
            }
        elif any(w in q for w in ["customer", "high value", "spent more", "tier", "who spent"]):
            return {
                "sql": """SELECT c.customer_id,
       c.first_name || ' ' || c.last_name AS customer_name,
       c.email,
       c.customer_tier,
       c.city,
       COUNT(o.order_id) AS total_orders,
       ROUND(SUM(o.total_amount), 2) AS total_spent
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status != 'Cancelled'
GROUP BY c.customer_id, customer_name, c.email, c.customer_tier, c.city
HAVING SUM(o.total_amount) > 500
ORDER BY total_spent DESC;""",
                "explanation": "Identifies loyal high-value customers who have spent over $500 in total across all valid orders.",
                "chart_recommendation": {
                    "chart_type": "bar",
                    "x_column": "customer_name",
                    "y_column": "total_spent",
                    "title": "Top Customers by Spend"
                }
            }
        elif any(w in q for w in ["stock", "inventory", "low stock"]):
            return {
                "sql": """SELECT name AS product_name,
       category,
       price,
       stock_quantity
FROM products
WHERE stock_quantity < 50
ORDER BY stock_quantity ASC;""",
                "explanation": "Filters products whose inventory level is below 50 units, sorted from lowest stock to highest for replenishment priority.",
                "chart_recommendation": {
                    "chart_type": "bar",
                    "x_column": "product_name",
                    "y_column": "stock_quantity",
                    "title": "Low Stock Items (< 50 units)"
                }
            }
        elif any(w in q for w in ["status", "order status", "breakdown"]):
            return {
                "sql": """SELECT status,
       COUNT(*) AS order_count,
       ROUND(SUM(total_amount), 2) AS total_value
FROM orders
GROUP BY status
ORDER BY order_count DESC;""",
                "explanation": "Shows the breakdown of orders by their current fulfillment status.",
                "chart_recommendation": {
                    "chart_type": "pie",
                    "x_column": "status",
                    "y_column": "order_count",
                    "title": "Orders Breakdown by Status"
                }
            }

    # If active tables exist in the connected database, fallback to the first active table
    if tables:
        first_t = tables[0]
        quote = '"' if settings.db.mode == "postgres" else ''
        return {
            "sql": f"SELECT * FROM {quote}{first_t}{quote} LIMIT 10;",
            "explanation": f"Retrieved sample records from table '{first_t}'. (⚠️ Configure Gemini API Key in Settings for natural language queries on any schema).",
            "chart_recommendation": {
                "chart_type": "table",
                "x_column": "",
                "y_column": "",
                "title": f"Recent Records from {first_t}"
            }
        }

    # Generic fallback
    return {
        "sql": "SELECT 1 AS status;",
        "explanation": "Please connect a database or provide a Gemini API Key in Settings to generate SQL.",
        "chart_recommendation": {
            "chart_type": "table",
            "x_column": "",
            "y_column": "",
            "title": "Query Results"
        }
    }


async def generate_completion(prompt: str, system_instruction: str = "") -> str:
    """Dispatches the prompt to the configured AI provider."""
    provider = settings.ai.provider
    clean_question = prompt.split("User Question:")[-1].strip() if "User Question:" in prompt else prompt

    if provider == "gemini":
        if not settings.ai.gemini_api_key:
            # Check if mock fallback is appropriate
            return json.dumps(mock_text_to_sql(clean_question))
        return await call_gemini(
            prompt=prompt,
            system_instruction=system_instruction,
            api_key=settings.ai.gemini_api_key,
            model=settings.ai.gemini_model
        )
    elif provider == "openai":
        if not settings.ai.openai_api_key:
            return json.dumps(mock_text_to_sql(clean_question))
        return await call_openai(
            prompt=prompt,
            system_instruction=system_instruction,
            api_key=settings.ai.openai_api_key,
            model=settings.ai.openai_model
        )
    elif provider == "ollama":
        return await call_ollama(
            prompt=prompt,
            system_instruction=system_instruction,
            base_url=settings.ai.ollama_base_url,
            model=settings.ai.ollama_model
        )
    else:
        # Mock mode
        return json.dumps(mock_text_to_sql(clean_question))
