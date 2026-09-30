"""Role Based Access Control.
Har document ka ek access level hota hai; har role ko kuch levels ki permission hai.
Filtering retrieval SE PEHLE hoti hai, taake unauthorized text kabhi LLM tak na pahunche."""
import hashlib, time
import jwt
from fastapi import HTTPException, Header
from . import config

ROLE_PERMISSIONS = {
    "admin":    {"public", "hr", "finance", "engineering"},
    "hr":       {"public", "hr"},
    "finance":  {"public", "finance"},
    "engineer": {"public", "engineering"},
    "employee": {"public"},
}

def _h(p): return hashlib.sha256(p.encode()).hexdigest()

# Demo users. Real project mein database use karein.
USERS = {
    "admin": {"password": _h("admin123"), "role": "admin"},
    "sara":  {"password": _h("hr123"),    "role": "hr"},
    "ali":   {"password": _h("fin123"),   "role": "finance"},
    "usman": {"password": _h("eng123"),   "role": "engineer"},
    "guest": {"password": _h("guest123"), "role": "employee"},
}

def authenticate(username: str, password: str):
    u = USERS.get(username)
    if not u or u["password"] != _h(password):
        return None
    return {"username": username, "role": u["role"]}

def create_token(user: dict) -> str:
    payload = {**user, "exp": time.time() + config.JWT_EXPIRE_MINUTES * 60}
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGO)

def get_current_user(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    try:
        data = jwt.decode(authorization[7:], config.JWT_SECRET, algorithms=[config.JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    return {"username": data["username"], "role": data["role"]}

def allowed_levels(role: str) -> set:
    return ROLE_PERMISSIONS.get(role, set())
