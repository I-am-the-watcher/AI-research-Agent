
import os
from dotenv import load_dotenv

load_dotenv()

# AI Models
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")

# API Credentials
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Langfuse Observability
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv(
    "LANGFUSE_HOST",
    "https://cloud.langfuse.com"
)

# Research Configuration
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "2"))

TAVILY_MONTHLY_LIMIT = int(
    os.getenv("TAVILY_MONTHLY_LIMIT", "900")
)

TAVILY_SEARCH_DEPTH = os.getenv("TAVILY_SEARCH_DEPTH", "basic")

TAVILY_RESULTS_PER_SEARCH = int(
    os.getenv("TAVILY_RESULTS_PER_SEARCH", "3")
)

MAX_SUBTASKS = int(os.getenv("MAX_SUBTASKS", "3"))
