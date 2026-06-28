"""HTTP Request Tool — outbound HTTP calls with SSRF blocking and allowlist enforcement."""

import logging
import re
from typing import Any, Dict, List, Optional
from ipaddress import ip_address, ip_network
import httpx

logger = logging.getLogger(__name__)

# SSRF blocklist — private/reserved IP ranges
_BLOCKED_NETWORKS = [
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    ip_network("127.0.0.0/8"),
    ip_network("169.254.0.0/16"),
    ip_network("100.64.0.0/10"),
    ip_network("::1/128"),
    ip_network("fc00::/7"),
]

_DEFAULT_TIMEOUT = 15.0
_MAX_RESPONSE_BYTES = 50_000  # 50KB response cap


def _is_blocked_host(hostname: str) -> bool:
    """Returns True if the hostname resolves to a blocked (private/SSRF-risk) address."""
    try:
        addr = ip_address(hostname)
        for net in _BLOCKED_NETWORKS:
            if addr in net:
                return True
        return False
    except ValueError:
        # Hostname is not a raw IP — DNS resolution would be needed for full SSRF protection.
        # Block known internal hostnames
        blocked_patterns = [
            r"localhost",
            r"internal",
            r"\.local$",
            r"metadata\.google\.internal",
            r"169\.254\.",
        ]
        for pat in blocked_patterns:
            if re.search(pat, hostname, re.IGNORECASE):
                return True
        return False


async def http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
    allowed_domains: Optional[List[str]] = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """
    Makes an outbound HTTP request with SSRF protection.

    Args:
        url: Target URL
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Optional request headers (secrets must not be injected by agent)
        body: Optional JSON body for POST/PUT
        allowed_domains: If provided, only these domains are permitted
        timeout: Request timeout in seconds
    """
    if not url:
        return {"status": "error", "message": "url is required"}

    method = method.upper()
    if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
        return {"status": "error", "message": f"HTTP method '{method}' is not allowed"}

    # Extract hostname for SSRF check
    try:
        parsed = httpx.URL(url)
        hostname = parsed.host
    except Exception:
        return {"status": "error", "message": f"Invalid URL: {url}"}

    # SSRF protection
    if _is_blocked_host(hostname):
        logger.warning(f"SSRF attempt blocked: {url} resolves to a private/blocked address")
        return {
            "status": "error",
            "message": f"Access to '{hostname}' is blocked (private/internal network).",
        }

    # Domain allowlist check
    if allowed_domains:
        if not any(hostname.endswith(domain) for domain in allowed_domains):
            return {
                "status": "error",
                "message": (
                    f"Domain '{hostname}' is not in the allowed list: {allowed_domains}"
                ),
            }

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers or {},
                json=body if method in ("POST", "PUT", "PATCH") else None,
            )

        # Cap response size
        content = response.text[:_MAX_RESPONSE_BYTES]
        if len(response.text) > _MAX_RESPONSE_BYTES:
            content += "\n... [response truncated]"

        logger.info(f"HTTP {method} {url} → {response.status_code}")
        return {
            "status": "success",
            "status_code": response.status_code,
            "content": content,
            "headers": dict(response.headers),
        }

    except httpx.TimeoutException:
        return {"status": "error", "message": f"Request to {url} timed out after {timeout}s"}
    except Exception as e:
        logger.error(f"HTTP request to {url} failed: {e}")
        return {"status": "error", "message": str(e)}
