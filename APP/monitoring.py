"""Structured logging + in-memory metrics + SQLite audit trail + rate limiting."""
import json, logging, sqlite3, time, threading
from collections import defaultdict, deque
from . import config

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("rag")

_lock = threading.Lock()
counters = defaultdict(int)
latencies = deque(maxlen=1000)
_requests = defaultdict(deque)

def log_event(event: str, **kw):
    logger.info(json.dumps({"ts": time.time(), "event": event, **kw}))

def incr(name: str, n: int = 1):
    with _lock: counters[name] += n

def observe_latency(ms: float):
    with _lock: latencies.append(ms)

def metrics_snapshot() -> dict:
    with _lock:
        lat = sorted(latencies)
        pct = lambda q: lat[min(int(len(lat) * q), len(lat) - 1)] if lat else 0
        return {"counters": dict(counters),
                "latency_ms": {"count": len(lat), "avg": round(sum(lat)/len(lat), 2) if lat else 0,
                               "p50": round(pct(0.5), 2), "p95": round(pct(0.95), 2)}}

def prometheus_text() -> str:
    s = metrics_snapshot()
    lines = [f"rag_{k} {v}" for k, v in s["counters"].items()]
    lines += [f"rag_latency_ms_{k} {v}" for k, v in s["latency_ms"].items()]
    return "\n".join(lines) + "\n"

def rate_limited(user: str) -> bool:
    now = time.time(); q = _requests[user]
    while q and now - q[0] > 60: q.popleft()
    if len(q) >= config.RATE_LIMIT_PER_MIN: return True
    q.append(now); return False

def _db():
    c = sqlite3.connect(config.AUDIT_DB)
    c.execute("""CREATE TABLE IF NOT EXISTS audit(
        id INTEGER PRIMARY KEY, ts REAL, username TEXT, role TEXT, query TEXT,
        status TEXT, reason TEXT, sources TEXT, latency_ms REAL)""")
    return c

def audit(username, role, query, status, reason, sources, latency_ms):
    c = _db()
    with c:
        c.execute("INSERT INTO audit(ts,username,role,query,status,reason,sources,latency_ms) VALUES(?,?,?,?,?,?,?,?)",
                  (time.time(), username, role, query, status, reason, json.dumps(sources), latency_ms))
    c.close()

def recent_audit(limit=50):
    c = _db()
    rows = c.execute("SELECT ts,username,role,query,status,reason,sources,latency_ms FROM audit ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    keys = ["ts", "username", "role", "query", "status", "reason", "sources", "latency_ms"]
    return [dict(zip(keys, r)) for r in rows]
