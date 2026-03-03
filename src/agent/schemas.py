from pydantic import BaseModel
from typing import Optional, List

# Incoming Webhook Callback Payload
class AnalyzeCallback(BaseModel):
    report_id: str
    verdict: str  # e.g., 'escalate', 'auto-approve', 'auto-reject'
    pii_found: bool
    redacted_text: Optional[str] = None
    integral_score: float  # confidence score
    flags: List[str] = []
