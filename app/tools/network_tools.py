from __future__ import annotations

import socket
from urllib.request import Request, urlopen

from langchain_core.tools import tool

USER_AGENT = "langchain-001-agent/1.0"


@tool
def get_local_ip() -> str:
    """Return the preferred local outbound IPv4 address."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception as exc:
        return f"Local IP lookup failed: {exc}"
    finally:
        sock.close()


@tool
def get_public_ip() -> str:
    """Return the public IP address using an external IP echo service."""
    request = Request("https://api.ipify.org", headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8", errors="replace").strip()
    except Exception as exc:
        return f"Public IP lookup failed: {exc}"
