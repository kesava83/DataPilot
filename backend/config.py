import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class DBConfig(BaseModel):
    mode: Literal["postgres", "sample"] = "sample"
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    database: str = os.getenv("DB_NAME", "postgres")
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "")
    sslmode: str = os.getenv("DB_SSLMODE", "prefer")
    schema_name: str = os.getenv("DB_SCHEMA", "public")

    @property
    def connection_url(self) -> str:
        if self.mode == "sample":
            return "sqlite:///./sample_ecommerce.db"
        # PostgreSQL URL using psycopg3
        pw = f":{self.password}" if self.password else ""
        return f"postgresql+psycopg://{self.user}{pw}@{self.host}:{self.port}/{self.database}?sslmode={self.sslmode}"


class AIConfig(BaseModel):
    provider: Literal["gemini", "openai", "ollama", "mock"] = os.getenv("AI_PROVIDER", "gemini")  # type: ignore
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3:latest")


class AppSettings:
    def __init__(self):
        self.db = DBConfig(
            mode=os.getenv("DB_MODE", "sample"),  # type: ignore
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            sslmode=os.getenv("DB_SSLMODE", "prefer"),
            schema_name=os.getenv("DB_SCHEMA", "public"),
        )
        self.ai = AIConfig(
            provider=os.getenv("AI_PROVIDER", "gemini"),  # type: ignore
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3:latest"),
        )
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "8000"))
        self.read_only_mode = True  # Safety default


settings = AppSettings()
