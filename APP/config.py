import os
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGO = "HS256"
JWT_EXPIRE_MINUTES = 60
TOP_K = 3
MIN_SCORE = 0.05            # isse kam similarity wale chunks ignore
MAX_QUERY_CHARS = 500
RATE_LIMIT_PER_MIN = 20     # per user
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "docs")
AUDIT_DB = os.getenv("AUDIT_DB", "audit.db")
