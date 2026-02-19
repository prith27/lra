"""Configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Sandbox API
SANDBOX_URL: str = os.getenv("SANDBOX_URL", "http://localhost:8000")

# LLM API
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# Database
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./data/agent_memory.db",
)

# Vector store
VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "./data/chroma_db")

# Ensure data directory exists
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)
