import logging
import time
from typing import Any, Optional

logger = logging.getLogger("omniflow.public_api.telemetry")

def log_public_telemetry(
    event_type: str,
    workspace_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
    latency_ms: Optional[float] = None,
    details: Optional[dict[str, Any]] = None
) -> None:
    """
    Standardized structured logging for Public API telemetry.
    This ensures logs are tenant-safe and explicitly structured without secrets.
    """
    payload = {
        "event_type": event_type,
        "workspace_id": workspace_id,
        "api_key_id": api_key_id,
    }
    if latency_ms is not None:
        payload["latency_ms"] = round(latency_ms, 2)
        
    if details:
        # Shallow copy to avoid mutating the original dict, ensure no secrets
        safe_details = details.copy()
        if "secret" in safe_details:
            del safe_details["secret"]
        if "password" in safe_details:
            del safe_details["password"]
        payload.update(safe_details)
        
    logger.info(
        f"Public API Telemetry: {event_type}",
        extra={"telemetry": payload}
    )

def log_business_telemetry(
    event_type: str,
    workspace_id: Optional[str] = None,
    latency_ms: Optional[float] = None,
    details: Optional[dict[str, Any]] = None
) -> None:
    """
    Standardized structured logging for Business Analyst telemetry.
    """
    payload = {
        "event_type": event_type,
        "workspace_id": workspace_id,
    }
    if latency_ms is not None:
        payload["latency_ms"] = round(latency_ms, 2)
        
    if details:
        payload.update(details)
        
    logger.info(
        f"Business Analyst Telemetry: {event_type}",
        extra={"telemetry": payload}
    )

class LatencyTracker:
    def __init__(self):
        self.start_time = time.perf_counter()

    def get_latency_ms(self) -> float:
        return (time.perf_counter() - self.start_time) * 1000.0
