from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from . import rbac, monitoring as mon
from .pipeline import answer_query

app = FastAPI(title="RAG with RBAC, Guardrails & Monitoring")

class LoginReq(BaseModel):
    username: str
    password: str

class AskReq(BaseModel):
    query: str

@app.post("/login")
def login(req: LoginReq):
    user = rbac.authenticate(req.username, req.password)
    if not user:
        mon.incr("login_failed")
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": rbac.create_token(user), "role": user["role"]}

@app.post("/ask")
def ask(req: AskReq, user=Depends(rbac.get_current_user)):
    return answer_query(user, req.query)

@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return mon.prometheus_text()

@app.get("/admin/audit")
def audit_log(limit: int = 50, user=Depends(rbac.get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Admin only")
    return mon.recent_audit(limit)

@app.get("/health")
def health():
    return {"ok": True}
