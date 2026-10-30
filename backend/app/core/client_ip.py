"""Client IP resolution honoring only configured trusted proxies (P3-11).

Fixes the Phase 0 finding: X-Forwarded-For was trusted unconditionally,
allowing rate-limit bypass via header spoofing.
"""

import ipaddress

from starlette.requests import Request


def client_ip_from(request: Request, trusted_cidrs: list[str]) -> str | None:
    """Resolve the real client IP.

    If the socket peer is not a trusted proxy, the peer address is authoritative
    and forwarded headers are ignored. If it is a trusted proxy, walk
    X-Forwarded-For right-to-left and take the first (rightmost) hop that is not
    itself a trusted proxy; if all hops are trusted, use the peer.
    """
    peer = request.client.host if request.client else None
    if not peer:
        return None
    try:
        networks = [ipaddress.ip_network(c.strip()) for c in trusted_cidrs if c.strip()]
    except ValueError:
        networks = []

    try:
        peer_addr = ipaddress.ip_address(peer)
    except ValueError:
        return peer

    if not any(peer_addr in n for n in networks):
        return peer

    xff = request.headers.get("x-forwarded-for")
    if not xff:
        return peer
    for hop in reversed([h.strip() for h in xff.split(",")]):
        try:
            addr = ipaddress.ip_address(hop)
        except ValueError:
            return peer
        if any(addr in n for n in networks):
            continue  # intermediate trusted proxy
        return str(addr)
    return peer
