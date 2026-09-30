import time
from . import guardrails, monitoring as mon
from .rag import Retriever, generate_answer, SYSTEM_PROMPT

retriever = Retriever()
REFUSAL = "Sorry, I couldn't find that information in the documents you have access to."

def answer_query(user: dict, query: str) -> dict:
    t0 = time.time()
    uname, role = user["username"], user["role"]
    mon.incr("requests_total")

    def finish(status, reason, answer, sources=()):
        ms = (time.time() - t0) * 1000
        mon.observe_latency(ms); mon.incr(f"status_{status}")
        mon.audit(uname, role, query[:300], status, reason, list(sources), ms)
        mon.log_event("query", user=uname, role=role, status=status, reason=reason, latency_ms=round(ms, 1))
        return {"answer": answer, "status": status, "reason": reason, "sources": list(sources)}

    if mon.rate_limited(uname):
        return finish("blocked", "rate_limited", "Too many requests. Please wait a minute.")

    g = guardrails.check_input(query)
    if not g.allowed:
        mon.incr(f"guard_input_{g.reason}")
        return finish("blocked", g.reason, "Your request was blocked by safety guardrails.")

    chunks = retriever.search(g.text, role)
    if not chunks:
        mon.incr("no_context")
        return finish("no_answer", "no_authorized_context", REFUSAL)

    raw = generate_answer(g.text, chunks)
    out = guardrails.check_output(raw, chunks, SYSTEM_PROMPT)
    if not out.allowed:
        mon.incr(f"guard_output_{out.reason.split(':')[0]}")
        return finish("blocked", out.reason, REFUSAL)

    return finish("ok", out.reason, out.text, sorted({c["source"] for c in chunks}))
