"""Input + Output guardrails."""
import re
from dataclasses import dataclass
from . import config

INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|above|prior) (instructions|rules)",
    r"disregard (the )?(system|previous) (prompt|instructions)",
    r"reveal (your |the )?(system )?prompt",
    r"you are now (dan|jailbroken|unrestricted)",
    r"act as (an? )?(unrestricted|admin|root)",
    r"bypass (the )?(security|access|rbac|guardrails?)",
    r"pretend (you have|to have) (admin|full) access",
]
BLOCKED_TOPICS = [r"\bbuild (a )?bomb\b", r"\bhow to hack\b", r"\bmake (a )?weapon\b"]

PII_PATTERNS = {
    "EMAIL": r"[\w\.-]+@[\w\.-]+\.\w+",
    "CNIC":  r"\b\d{5}-\d{7}-\d\b",
    "PHONE": r"(?<!\d)(\+92|0)3\d{2}[-\s]?\d{7}(?!\d)",
    "CARD":  r"\b(?:\d[ -]?){13,16}\b",
}

@dataclass
class GuardResult:
    allowed: bool
    reason: str = ""
    text: str = ""

def redact_pii(text: str):
    found = []
    for label, pat in PII_PATTERNS.items():
        if re.search(pat, text):
            found.append(label)
            text = re.sub(pat, f"[{label}_REDACTED]", text)
    return text, found

def check_input(query: str) -> GuardResult:
    q = (query or "").strip()
    if not q:
        return GuardResult(False, "empty_query")
    if len(q) > config.MAX_QUERY_CHARS:
        return GuardResult(False, "query_too_long")
    low = q.lower()
    for p in INJECTION_PATTERNS:
        if re.search(p, low):
            return GuardResult(False, "prompt_injection")
    for p in BLOCKED_TOPICS:
        if re.search(p, low):
            return GuardResult(False, "blocked_topic")
    clean, pii = redact_pii(q)          # user ki PII LLM/logs tak na jaye
    return GuardResult(True, "pii_redacted:" + ",".join(pii) if pii else "ok", clean)

def check_output(answer: str, context_chunks: list, system_prompt: str = "") -> GuardResult:
    if system_prompt and system_prompt[:40].lower() in answer.lower():
        return GuardResult(False, "system_prompt_leak")
    clean, pii = redact_pii(answer)
    # grounding: answer ke content words ka kam az kam 30% context mein hona chahiye
    words = set(re.findall(r"[a-z]{4,}", clean.lower()))
    ctx = " ".join(c["text"].lower() for c in context_chunks)
    if words and context_chunks:
        overlap = sum(1 for w in words if w in ctx) / len(words)
        if overlap < 0.3:
            return GuardResult(False, f"low_grounding:{overlap:.2f}")
    return GuardResult(True, "pii_redacted:" + ",".join(pii) if pii else "ok", clean)
