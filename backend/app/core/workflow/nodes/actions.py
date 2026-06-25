"""Action nodes implementation."""

import httpx
from typing import Any, Dict
from backend.app.core.workflow.nodes.base import BaseNodeExecutor, NodeExecutionResult


class WebhookAction(BaseNodeExecutor):
    async def execute(self, context: Dict[str, Any]) -> NodeExecutionResult:
        url = self.config.get("url")
        method = self.config.get("method", "POST")
        payload = self.config.get("payload", {})
        headers = self.config.get("headers", {})

        if not url:
            return NodeExecutionResult.failed({"error": "Missing URL configuration"})

        import ipaddress
        from urllib.parse import urlparse
        import socket

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                raise ValueError("Invalid URL")

            ip_addr = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_addr)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
                return NodeExecutionResult.failed({"error": "SSRF protected: Access to internal networks is forbidden."})
        except Exception as e:
            return NodeExecutionResult.failed({"error": f"SSRF check failed: {str(e)}"})

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return NodeExecutionResult.success(output={"status_code": response.status_code, "response": response.text})
        except httpx.RequestError as exc:
            return NodeExecutionResult.failed({"error": f"Request failed: {str(exc)}"})
        except httpx.HTTPStatusError as exc:
            return NodeExecutionResult.failed({"error": f"HTTP {exc.response.status_code} - {exc.response.text}"})

class AddTagAction(BaseNodeExecutor):
    async def execute(self, context: Dict[str, Any]) -> NodeExecutionResult:
        tag = self.config.get("tag")
        if not tag:
            return NodeExecutionResult.failed({"error": "Tag not configured"})
        return NodeExecutionResult.success(output={"added_tag": tag})
