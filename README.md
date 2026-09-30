# RAG with RBAC, Guardrails & Monitoring

## Run
    pip install -r requirements.txt
    python demo.py                      # server ke bina demo
    pytest -q tests                     # tests
    uvicorn app.main:app --reload       # API: http://127.0.0.1:8000/docs

Optional (real LLM answers): `export ANTHROPIC_API_KEY=...` (warna extractive fallback chalta hai).

## Demo users
admin/admin123, sara/hr123 (HR), ali/fin123 (Finance), usman/eng123 (Engineer), guest/guest123 (Employee)

## API
POST /login -> token | POST /ask (Bearer token) | GET /metrics | GET /admin/audit (admin only) | GET /health

## Architecture
Query -> JWT auth -> rate limit -> INPUT guardrails (injection, blocked topics, PII redact)
-> RBAC-filtered retrieval (TF-IDF) -> LLM -> OUTPUT guardrails (PII, prompt leak, grounding)
-> audit log (SQLite) + metrics + JSON logs

## Nayi document add karna
data/docs/ mein .txt file banayein, pehli line: `access: hr` (public/hr/finance/engineering)
