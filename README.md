# NLP AI - Natural Language PostgreSQL Studio

An interactive application that allows you to interact with your **PostgreSQL** database using plain natural language. Ask conversational business questions, automatically inspect schemas, generate optimized SQL queries, execute read-only queries with safety guards, and visualize results with interactive charts, tables, and AI insights.

---

## Key Features

- **Conversational Text-to-SQL**: Converts plain English questions (e.g., *"What are our top 5 best-selling products by revenue?"*) into accurate SQL queries.
- **Multi-Provider AI Support**:
  - **Google Gemini** (`gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-2.0-flash`)
  - **OpenAI** (`gpt-4o-mini`, `gpt-4o`)
  - **Ollama / Local LLMs** (`llama3:latest`, `mistral`, `deepseek-r1`)
  - **Built-in Smart Demo Mode**: Zero-configuration pattern-matching engine that lets you explore and query immediately even without an external API key!
- **Dynamic PostgreSQL Connection Manager**:
  - Connect to local or remote PostgreSQL databases (e.g., AWS RDS, Supabase, Neon, Render, Cloud SQL).
  - Test connection latency, verify server version, and detect tables in real-time.
  - Zero-restart switching: Switch between your PostgreSQL DB and the instant pre-populated eCommerce demo database anytime via the UI.
- **Interactive Schema Browser**:
  - Live table and column explorer with data types, primary keys, and foreign key relations.
  - One-click **Table Preview** (view the first 10 sample records).
  - Quick **"Query Table"** prompt shortcuts.
- **Smart Data Visualization**:
  - Automatic chart recommendation (Bar Charts, Line Trends, Doughnut/Pie distributions, Metric Cards).
  - Interactive data tables with sorting, pagination, and one-click **Export to CSV / JSON**.
- **Safety First**:
  - Read-only execution guards by default to prevent accidental `DROP`, `DELETE`, `TRUNCATE`, or `ALTER` operations.
  - Direct SQL Runner modal for reviewing, tweaking, and running custom queries.
- **Modern UI / UX**:
  - Premium dark/light themes with glassmorphism aesthetics, responsive split-screen layout, and fluid animations.

---

## Quick Start

### 1. Launch the Application

The virtual environment `.venv` and all dependencies are already set up in the project. Run:

```powershell
.venv\Scripts\python.exe run.py
```

Open your browser and navigate to:
**[http://localhost:8000](http://localhost:8000)**

---

## Connecting to Your PostgreSQL Database

You can connect your PostgreSQL database whenever you have the credentials ready:

### Method A: Via the Web UI (Recommended)
1. Open the app at `http://localhost:8000`.
2. Click the **Database Status Pill** in the top navigation bar or the **"Connection Settings"** button in the left sidebar.
3. Fill in your details:
   - **Host**: e.g., `localhost` or `db.example.com`
   - **Port**: `5432`
   - **Database Name**: e.g., `production_db`
   - **Username**: e.g., `postgres`
   - **Password**: your password
   - **SSL Mode**: `prefer` (or `require` for cloud databases like Supabase/Neon/RDS)
   - **Schema**: `public`
4. Click **"Test Connection"** to verify connectivity, latency, and detected tables.
5. Click **"Save & Connect"**. The schema browser and query engine will immediately synchronize with your database!

### Method B: Via `.env` File
You can also set default credentials in the `.env` file:

```env
DB_MODE=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_password
DB_SSLMODE=prefer
DB_SCHEMA=public
```

---

## Configuring AI / LLM Providers

Click the **AI Settings Pill** in the top navigation bar or configure via `.env`:

### 1. Google Gemini (Recommended)
- Get an API key for free at [Google AI Studio](https://aistudio.google.com/).
- Enter the key in the settings modal or set `GEMINI_API_KEY=AIzaSy...` in `.env`.
- Select your model (default: `gemini-2.5-flash`).

### 2. OpenAI
- Enter your OpenAI API key in the settings modal or set `OPENAI_API_KEY=sk-...` in `.env`.
- Select your model (`gpt-4o-mini` or `gpt-4o`).

### 3. Ollama (Local Offline AI)
- Ensure Ollama is running locally (`ollama run llama3`).
- Set Ollama Base URL (`http://localhost:11434`) and model name in settings.

### 4. Smart Demo Mode
- If no API key is provided, the app automatically runs in **Demo Mode**, answering business questions (e.g., top products, monthly revenue, high-value customers, low stock alerts) using built-in pattern recognition so you can experience the complete UI without any setup!

---

## Project Structure

```
db-chat/
├── .venv/                   # Python virtual environment
├── requirements.txt         # Pinned dependencies
├── .env.example             # Example environment variables
├── .env                     # Local configuration
├── run.py                   # One-click startup runner
├── backend/
│   ├── main.py              # FastAPI app & routing
│   ├── config.py            # Application & provider settings
│   ├── db/
│   │   ├── connection.py    # PostgreSQL & SQLite connection manager
│   │   ├── schema.py        # Schema introspection & LLM prompt formatter
│   │   └── sample_db.py     # Pre-populated eCommerce database generator
│   ├── ai/
│   │   ├── provider.py      # Multi-provider client (Gemini, OpenAI, Ollama, Demo)
│   │   ├── sql_generator.py # Text-to-SQL engine with JSON grounding
│   │   └── sql_explainer.py # Natural language analytical summarizer
│   └── routes/
│       ├── chat.py          # /api/chat & /api/query/execute
│       ├── db_routes.py     # /api/db/status, /api/db/test, /api/db/connect, /api/db/schema
│       └── config_routes.py # /api/config
└── frontend/
    ├── index.html           # Main studio dashboard
    ├── css/
    │   └── style.css        # Modern design system (dark/light, glassmorphism)
    └── js/
        ├── app.js           # Main coordinator & keyboard shortcuts
        ├── api.js           # REST API client
        ├── chat.js          # Chat stream, SQL cards & tab switcher
        ├── visualizer.js    # Data tables, pagination, Chart.js & CSV/JSON export
        ├── schema.js        # Sidebar schema explorer & table preview
        └── settings.js      # DB connection modal & AI provider modal
```
